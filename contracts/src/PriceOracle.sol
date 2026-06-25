// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

/// @notice Minimal Chainlink price-feed interface (T1.3 — Chainlink-first read path).
///         Declared locally rather than pulling in the chainlink/contracts package
///         so we add no new submodule dependency for one interface. This is the canonical
///         AggregatorV3Interface signature — Chainlink feeds (and Arc-native /
///         Chainlink-compatible aggregators) implement it verbatim.
///         Reference: https://docs.chain.link/data-feeds/api-reference
interface AggregatorV3Interface {
    /// @return The number of decimals the feed answer is reported in (USD feeds: 8).
    function decimals() external view returns (uint8);

    /// @notice Latest completed round of price data.
    /// @return roundId         The round ID the answer was computed in.
    /// @return answer          The price (signed; non-negative for a healthy feed).
    /// @return startedAt       Timestamp the round started.
    /// @return updatedAt       Timestamp the answer was last updated (staleness key).
    /// @return answeredInRound The round in which the answer was computed (legacy
    ///                         carry-over detector; answeredInRound < roundId means
    ///                         the answer is stale carried from a prior round).
    function latestRoundData()
        external
        view
        returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound);
}

/// @title PriceOracle
/// @notice Per-asset price oracle for any asset on Arc testnet. Prefers a Chainlink
///         `AggregatorV3Interface` feed when one is configured (T1.3); falls back to
///         the admin-fed value (backend oracle runner pushes via `setPrice`) for
///         assets that have no native Chainlink feed.
/// @dev    ⚠️ Funds-adjacent: this price flows straight into Vault / SyntheticVault
///         collateral math (`getPrice()` → 6-decimal USDC price). Read-path changes
///         here need a careful contract review (Chuan).
///
///         Read-path precedence (see `getPrice()`):
///           1. Chainlink feed (if `priceFeed != address(0)`), with staleness +
///              non-negative + round-completeness checks, scaled to 6 decimals.
///           2. Admin-fed `price` (the existing hackathon path), with its own
///              staleness check — used when no feed is configured.
///         The no-arg `getPrice()` signature is preserved so every existing consumer
///         (Vault, SyntheticVault, SyntheticFactory) and the backend keep working.
contract PriceOracle is Ownable {
    /// @notice Asset price in USDC (6 decimals). e.g. $392.60 → 392600000.
    ///         This is the *admin-fed* value (the fallback path). When a Chainlink
    ///         feed is configured, `getPrice()` reads the feed instead and this
    ///         field is not used for the live read. Kept public + named `price` so
    ///         the backend's on-chain reference read (`.price()`) keeps working.
    uint256 public price;

    /// @notice Human-readable label (e.g. "TSLA", "NVDA", "SPY")
    string public symbol;

    /// @notice Timestamp of the last price update
    uint256 public lastUpdated;

    /// @notice Maximum age before stale (24 hours — hackathon testnet, Circle daily limit)
    uint256 public constant MAX_STALENESS = 24 hours;

    /// @notice Address allowed to push price updates (e.g. Circle wallet)
    address public updater;

    /// @notice Chainlink (or Chainlink-compatible) price feed for this asset (T1.3).
    ///         When non-zero, `getPrice()` reads `latestRoundData()` from this feed
    ///         instead of the admin-fed `price`. Owner-set via `setPriceFeed`; set
    ///         back to `address(0)` to revert to the admin-fed fallback.
    AggregatorV3Interface public priceFeed;

    /// @notice Target decimals for the returned price — USDC's 6 decimals, matching
    ///         the admin-fed `price` convention and every consumer's math. Chainlink
    ///         USD feeds report 8 decimals, so the feed answer is rescaled to this.
    uint8 public constant PRICE_DECIMALS = 6;

    /// @notice Timestamp of the last *setPrice* update (0 until the first one).
    ///         Distinct from lastUpdated (which the constructor seeds) so the
    ///         updateCooldown applies only between two actual updater pushes —
    ///         not between deploy and the first push. forceSetPrice does not
    ///         touch this field; the cooldown only governs the setPrice path.
    uint256 public lastSetPriceTime;

    /// @notice Max allowed move per setPrice, in basis points vs the prior price.
    ///         Default 2000 bps (20%) — generous for a daily-update cadence but
    ///         blocks fat-finger / glitched-feed / compromised-key writes that
    ///         would otherwise flow straight into Vault.totalAssets().
    ///         Owner-configurable via setMaxDeviationBps; for a legitimately
    ///         gapped market the owner can use forceSetPrice (two-step escape
    ///         hatch) so the oracle can never be bricked permanently.
    uint256 public maxDeviationBps = 2000;

    /// @notice Basis-point denominator (100% = 10_000 bps)
    uint256 public constant BPS_DENOMINATOR = 10_000;

    /// @notice Hard cap on single forceSetPrice moves (900% = 10× max change per call).
    ///         Prevents pathological oracle manipulation; legitimate >10× gaps require
    ///         two sequential calls. Unlike setPrice's maxDeviationBps this constant is
    ///         not owner-configurable — it exists precisely to bound a compromised key.
    uint256 public constant FORCE_MAX_DEVIATION_BPS = 90_000;

    /// @notice Minimum spacing between two consecutive setPrice calls, in seconds.
    ///         setPrice already bounds a single move to maxDeviationBps, but with no
    ///         spacing an attacker could chain N max-deviation calls in one block to
    ///         ratchet the price arbitrarily (issue #587). Requiring a gap of at least
    ///         updateCooldown seconds between accepted updates blocks that intra-block
    ///         chaining and limits a compromised key to one bounded move per window,
    ///         giving the owner time to react (rotate the key / forceSetPrice).
    ///         Owner-configurable via setUpdateCooldown; forceSetPrice (owner escape
    ///         hatch) is exempt so the owner can always reprice out-of-band.
    ///         Default 30s — well above Arc's sub-second block time (so it defeats the
    ///         same-block ratchet this guards against) yet comfortably below the oracle
    ///         runner's 60s push cadence (ORACLE_INTERVAL_SECONDS), so legitimate
    ///         updates never trip it. Operators who slow the on-chain push cadence can
    ///         raise this toward MAX_UPDATE_COOLDOWN for a stronger rate limit.
    uint256 public updateCooldown = 30;

    /// @notice Upper bound on the owner-configurable cooldown (1 hour). Prevents the
    ///         owner from setting a cooldown so long that legitimate daily updates are
    ///         blocked, while still allowing the bound to be tuned for the deploy cadence.
    uint256 public constant MAX_UPDATE_COOLDOWN = 1 hours;

    event PriceUpdated(uint256 oldPrice, uint256 newPrice, uint256 timestamp);
    event PriceForced(uint256 oldPrice, uint256 newPrice, uint256 timestamp);
    event MaxDeviationBpsChanged(uint256 oldBps, uint256 newBps);
    event UpdaterChanged(address oldUpdater, address newUpdater);
    event UpdateCooldownChanged(uint256 oldCooldown, uint256 newCooldown);
    event PriceFeedChanged(address oldFeed, address newFeed);

    error StalePrice();
    error UnauthorizedUpdater();
    error ZeroPrice();
    error PriceDeviationTooLarge(uint256 oldPrice, uint256 newPrice, uint256 maxBps);
    error InvalidDeviationBound();
    error UpdateRateLimited(uint256 lastUpdated, uint256 cooldown, uint256 nowTs);
    error InvalidCooldown();
    // ── Chainlink read-path errors (T1.3) ──────────────────────────
    error NegativePrice(int256 answer); // feed reported answer <= 0
    error IncompleteRound(); // updatedAt == 0 → round not yet answered
    error StaleFeedRound(uint80 roundId, uint80 answeredInRound); // carried-over answer
    error InvalidFeedDecimals(uint8 decimals); // feed decimals would overflow scaling

    modifier onlyUpdater() {
        if (msg.sender != owner() && msg.sender != updater) revert UnauthorizedUpdater();
        _;
    }

    constructor(string memory _symbol, uint256 _initialPrice, address _owner) Ownable(_owner) {
        symbol = _symbol;
        price = _initialPrice;
        lastUpdated = block.timestamp;
        updater = _owner;
        emit PriceUpdated(0, _initialPrice, block.timestamp);
    }

    /// @notice Push a new price. Bounded: rejects zero and any move larger
    ///         than maxDeviationBps vs the prior price. If the market truly
    ///         gapped beyond the bound, the owner uses forceSetPrice (or
    ///         widens the bound via setMaxDeviationBps).
    function setPrice(uint256 _newPrice) external onlyUpdater {
        if (_newPrice == 0) revert ZeroPrice();
        // Rate-limit: require at least updateCooldown seconds between two
        // accepted setPrice pushes (issue #587). Skipped on the very first
        // push (lastSetPriceTime == 0). Combined with the per-call deviation
        // bound, this caps a compromised updater key to one bounded move per
        // cooldown window — it cannot chain many max-deviation calls in a block
        // to ratchet the price. forceSetPrice (owner escape hatch) is exempt.
        if (lastSetPriceTime != 0 && block.timestamp < lastSetPriceTime + updateCooldown) {
            revert UpdateRateLimited(lastSetPriceTime, updateCooldown, block.timestamp);
        }
        uint256 oldPrice = price;
        // Deviation bound only applies once a prior price exists; a zero
        // prior price (bootstrap) accepts any positive first price.
        if (oldPrice != 0) {
            uint256 diff = _newPrice > oldPrice ? _newPrice - oldPrice : oldPrice - _newPrice;
            if (diff * BPS_DENOMINATOR > oldPrice * maxDeviationBps) {
                revert PriceDeviationTooLarge(oldPrice, _newPrice, maxDeviationBps);
            }
        }
        price = _newPrice;
        lastUpdated = block.timestamp;
        lastSetPriceTime = block.timestamp;
        emit PriceUpdated(oldPrice, _newPrice, block.timestamp);
    }

    /// @notice Emergency override — owner-only escape hatch for legitimately
    ///         gapped markets (e.g. a >maxDeviationBps overnight move). Bounded
    ///         by FORCE_MAX_DEVIATION_BPS (900% / 10×) when a prior price exists;
    ///         a legitimate >10× gap requires two sequential calls. Emits a
    ///         distinct event so forced updates are auditable on-chain.
    function forceSetPrice(uint256 _newPrice) external onlyOwner {
        if (_newPrice == 0) revert ZeroPrice();
        uint256 oldPrice = price;
        if (oldPrice != 0) {
            uint256 diff = _newPrice > oldPrice ? _newPrice - oldPrice : oldPrice - _newPrice;
            if (diff * BPS_DENOMINATOR > oldPrice * FORCE_MAX_DEVIATION_BPS) {
                revert PriceDeviationTooLarge(oldPrice, _newPrice, FORCE_MAX_DEVIATION_BPS);
            }
        }
        price = _newPrice;
        lastUpdated = block.timestamp;
        emit PriceForced(oldPrice, _newPrice, block.timestamp);
    }

    /// @notice Adjust the per-update deviation bound. Must be in (0, 10_000];
    ///         a zero bound would brick setPrice entirely and >100% is
    ///         meaningless (use forceSetPrice for gap recovery instead).
    function setMaxDeviationBps(uint256 _maxDeviationBps) external onlyOwner {
        if (_maxDeviationBps == 0 || _maxDeviationBps > BPS_DENOMINATOR) revert InvalidDeviationBound();
        uint256 old = maxDeviationBps;
        maxDeviationBps = _maxDeviationBps;
        emit MaxDeviationBpsChanged(old, _maxDeviationBps);
    }

    /// @notice Adjust the minimum spacing between setPrice calls (issue #587).
    ///         Bounded above by MAX_UPDATE_COOLDOWN so the owner cannot set a
    ///         cooldown long enough to block legitimate daily updates. A value
    ///         of 0 disables rate-limiting (the per-call deviation bound still
    ///         applies) — a deliberate, owner-only choice.
    function setUpdateCooldown(uint256 _cooldown) external onlyOwner {
        if (_cooldown > MAX_UPDATE_COOLDOWN) revert InvalidCooldown();
        uint256 old = updateCooldown;
        updateCooldown = _cooldown;
        emit UpdateCooldownChanged(old, _cooldown);
    }

    function setUpdater(address _updater) external onlyOwner {
        address old = updater;
        updater = _updater;
        emit UpdaterChanged(old, _updater);
    }

    /// @notice Configure (or clear) the Chainlink feed for this asset (T1.3).
    ///         Owner-only. Pass `address(0)` to disable the feed and fall back to
    ///         the admin-fed `price`. When a non-zero feed is set, its `decimals()`
    ///         is validated up front so a feed that would overflow the scaling math
    ///         (decimals > 36) is rejected at configuration time rather than on read.
    /// @dev    ⚠️ Funds-adjacent: pointing this at the wrong feed silently reprices
    ///         every vault that reads this oracle. Verify the feed address +
    ///         denomination (must be the asset/USD pair) before calling. Does NOT
    ///         re-validate the feed's *answer* here (a feed can be healthy at config
    ///         time and stale later) — staleness is enforced on every `getPrice()`.
    function setPriceFeed(address _feed) external onlyOwner {
        if (_feed != address(0)) {
            // Probe decimals() so a non-conforming or overflow-prone feed can't be
            // wired in. PRICE_DECIMALS (6) + 36 keeps the up-scale (10 ** (6 - d))
            // and down-scale (10 ** (d - 6)) factors well inside uint256.
            uint8 feedDecimals = AggregatorV3Interface(_feed).decimals();
            if (feedDecimals > 36) revert InvalidFeedDecimals(feedDecimals);
        }
        address old = address(priceFeed);
        priceFeed = AggregatorV3Interface(_feed);
        emit PriceFeedChanged(old, _feed);
    }

    /// @notice Current asset price in USDC 6-decimal units.
    ///         Prefers the Chainlink feed when configured (T1.3); otherwise returns
    ///         the admin-fed `price`. Reverts (never returns a bad price) when the
    ///         active source is stale or invalid — consumers treat a revert as
    ///         "do not trade", so a bad feed blocks rather than misprices.
    /// @dev    Signature unchanged (no-arg) so Vault / SyntheticVault /
    ///         SyntheticFactory keep compiling and behaving identically.
    function getPrice() external view returns (uint256) {
        if (address(priceFeed) != address(0)) {
            return _readChainlink();
        }
        // Admin-fed fallback (assets with no native Chainlink feed).
        if (block.timestamp > lastUpdated + MAX_STALENESS) revert StalePrice();
        return price;
    }

    /// @notice True when the *active* price source is fresh (feed if configured,
    ///         else the admin-fed value). View-safe: never reverts; the Chainlink
    ///         branch returns false instead of bubbling a revert so callers can
    ///         probe freshness without a try/catch.
    function isFresh() external view returns (bool) {
        if (address(priceFeed) != address(0)) {
            try this.getPrice() returns (uint256) {
                return true;
            } catch {
                return false;
            }
        }
        return block.timestamp <= lastUpdated + MAX_STALENESS;
    }

    /// @notice Read + validate + scale the Chainlink feed answer to 6 decimals.
    /// @dev    Funds-safety checks, in order — any failure reverts (fail-closed):
    ///           • answer > 0           — reject zero / negative prices (NegativePrice)
    ///           • updatedAt != 0       — reject an unanswered/incomplete round
    ///                                    (IncompleteRound)
    ///           • answeredInRound >= roundId — reject a carried-over stale answer
    ///                                    from a prior round (StaleFeedRound)
    ///           • block.timestamp - updatedAt <= MAX_STALENESS — reject a feed that
    ///                                    has not updated within the staleness window
    ///                                    (StalePrice), the same bound the admin path
    ///                                    uses.
    ///         Then scale `answer` from the feed's reported decimals to PRICE_DECIMALS
    ///         (6). USD feeds report 8 decimals → divide by 100; a hypothetical
    ///         sub-6-decimal feed multiplies up. `decimals()` is bounded at config
    ///         time (<= 36) so neither scaling factor overflows.
    function _readChainlink() internal view returns (uint256) {
        (uint80 roundId, int256 answer,, uint256 updatedAt, uint80 answeredInRound) = priceFeed.latestRoundData();

        if (answer <= 0) revert NegativePrice(answer);
        if (updatedAt == 0) revert IncompleteRound();
        if (answeredInRound < roundId) revert StaleFeedRound(roundId, answeredInRound);
        if (block.timestamp > updatedAt + MAX_STALENESS) revert StalePrice();

        uint256 rawPrice = uint256(answer); // safe: answer > 0 checked above
        uint8 feedDecimals = priceFeed.decimals();

        if (feedDecimals == PRICE_DECIMALS) {
            return rawPrice;
        } else if (feedDecimals > PRICE_DECIMALS) {
            // e.g. 8-decimal USD feed → /100 to reach 6 decimals.
            return rawPrice / (10 ** (feedDecimals - PRICE_DECIMALS));
        } else {
            // Sub-6-decimal feed (rare) → scale up to 6 decimals.
            return rawPrice * (10 ** (PRICE_DECIMALS - feedDecimals));
        }
    }
}
