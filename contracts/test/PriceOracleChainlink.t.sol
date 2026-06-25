// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/PriceOracle.sol";

/// @dev Minimal mock implementing AggregatorV3Interface so we can drive the
///      Chainlink read path deterministically — feed answer, decimals, and the
///      round metadata (roundId / updatedAt / answeredInRound) are all settable.
contract MockAggregator is AggregatorV3Interface {
    uint8 internal _decimals;
    int256 internal _answer;
    uint80 internal _roundId;
    uint256 internal _updatedAt;
    uint80 internal _answeredInRound;

    constructor(uint8 d, int256 answer, uint256 updatedAt) {
        _decimals = d;
        _answer = answer;
        _updatedAt = updatedAt;
        _roundId = 1;
        _answeredInRound = 1;
    }

    function decimals() external view override returns (uint8) {
        return _decimals;
    }

    function latestRoundData()
        external
        view
        override
        returns (uint80, int256, uint256, uint256, uint80)
    {
        return (_roundId, _answer, _updatedAt, _updatedAt, _answeredInRound);
    }

    // ── Test setters ─────────────────────────────────────────────
    function setAnswer(int256 a) external {
        _answer = a;
    }

    function setUpdatedAt(uint256 t) external {
        _updatedAt = t;
    }

    function setRound(uint80 roundId, uint80 answeredInRound) external {
        _roundId = roundId;
        _answeredInRound = answeredInRound;
    }
}

/// @dev T1.3 — Chainlink-first read-path tests for PriceOracle.
///      Covers: feed-backed read (with 8→6 decimal scaling), staleness rejection,
///      admin fallback when no feed is configured, and the funds-safety guards
///      (negative/zero answer, incomplete round, carried-over stale round,
///      decimals overflow bound). The no-arg getPrice() signature is preserved,
///      so these assertions exercise the exact path Vault/SyntheticVault read.
contract PriceOracleChainlinkTest is Test {
    PriceOracle public oracle;
    MockAggregator public feed;

    address public owner = address(0x1);
    address public alice = address(0x2);

    uint256 constant INITIAL_PRICE = 392_600_000; // $392.60 (6 dec, admin-fed)

    // Chainlink USD feeds report 8 decimals. $392.60 → 39_260_000_000.
    uint8 constant FEED_DECIMALS = 8;
    int256 constant FEED_ANSWER = 39_260_000_000; // $392.60 @ 8 dec
    uint256 constant EXPECTED_6DEC = 392_600_000; // $392.60 @ 6 dec (scaled down)

    function setUp() public {
        // Pin a baseline well above MAX_STALENESS so "now - updatedAt" arithmetic
        // is unambiguous and we can warp backward/forward freely.
        vm.warp(1_000_000);
        vm.prank(owner);
        oracle = new PriceOracle("TSLA", INITIAL_PRICE, owner);
        feed = new MockAggregator(FEED_DECIMALS, FEED_ANSWER, block.timestamp);
    }

    // ─── Admin fallback (no feed configured) ─────────────────────────

    function test_admin_fallback_when_no_feed() public view {
        // Default state: no feed set → getPrice() returns the admin-fed value.
        assertEq(address(oracle.priceFeed()), address(0));
        assertEq(oracle.getPrice(), INITIAL_PRICE);
        assertTrue(oracle.isFresh());
    }

    function test_admin_fallback_reverts_when_stale() public {
        // Warp past MAX_STALENESS with no feed → admin path reverts StalePrice.
        vm.warp(block.timestamp + oracle.MAX_STALENESS() + 1);
        vm.expectRevert(PriceOracle.StalePrice.selector);
        oracle.getPrice();
        assertFalse(oracle.isFresh());
    }

    // ─── Feed-backed read ────────────────────────────────────────────

    function test_feed_backed_read_scales_8dec_to_6dec() public {
        vm.prank(owner);
        oracle.setPriceFeed(address(feed));
        assertEq(address(oracle.priceFeed()), address(feed));
        // 8-decimal $392.60 feed answer → 6-decimal 392_600_000.
        assertEq(oracle.getPrice(), EXPECTED_6DEC);
        assertTrue(oracle.isFresh());
    }

    function test_feed_takes_precedence_over_admin_price() public {
        // Admin price is $392.60; point the feed at a *different* value ($500)
        // and confirm getPrice() returns the FEED value, proving precedence.
        vm.prank(owner);
        oracle.setPriceFeed(address(feed));
        feed.setAnswer(50_000_000_000); // $500.00 @ 8 dec
        assertEq(oracle.getPrice(), 500_000_000); // $500.00 @ 6 dec
        // Admin-fed `price` storage is untouched.
        assertEq(oracle.price(), INITIAL_PRICE);
    }

    function test_feed_with_6_decimals_no_scaling() public {
        MockAggregator feed6 = new MockAggregator(6, 392_600_000, block.timestamp);
        vm.prank(owner);
        oracle.setPriceFeed(address(feed6));
        assertEq(oracle.getPrice(), 392_600_000);
    }

    function test_feed_with_sub6_decimals_scales_up() public {
        // 2-decimal feed: $392.60 → 39260 @ 2 dec → 392_600_000 @ 6 dec.
        MockAggregator feed2 = new MockAggregator(2, 39_260, block.timestamp);
        vm.prank(owner);
        oracle.setPriceFeed(address(feed2));
        assertEq(oracle.getPrice(), 392_600_000);
    }

    function test_clearing_feed_reverts_to_admin() public {
        vm.prank(owner);
        oracle.setPriceFeed(address(feed));
        assertEq(oracle.getPrice(), EXPECTED_6DEC);
        // Clear the feed → back to the admin-fed value.
        vm.prank(owner);
        oracle.setPriceFeed(address(0));
        assertEq(address(oracle.priceFeed()), address(0));
        assertEq(oracle.getPrice(), INITIAL_PRICE);
    }

    // ─── Staleness rejection (the core T1.3 funds-safety check) ──────

    function test_feed_staleness_rejection() public {
        vm.prank(owner);
        oracle.setPriceFeed(address(feed));
        // Pin the feed's updatedAt, then warp `now` to one second beyond the
        // staleness window → getPrice() must revert StalePrice (fail-closed).
        uint256 feedTs = block.timestamp; // 1_000_000 (pinned in setUp)
        feed.setUpdatedAt(feedTs);
        uint256 maxStaleness = oracle.MAX_STALENESS();
        vm.warp(feedTs + maxStaleness + 1); // now - updatedAt = MAX_STALENESS + 1
        vm.expectRevert(PriceOracle.StalePrice.selector);
        oracle.getPrice();
        // isFresh() reports false without bubbling the revert.
        assertFalse(oracle.isFresh());
    }

    function test_feed_fresh_at_exact_staleness_boundary() public {
        vm.prank(owner);
        oracle.setPriceFeed(address(feed));
        // updatedAt exactly MAX_STALENESS ago is still fresh (strict > check).
        uint256 ts = block.timestamp;
        feed.setUpdatedAt(ts);
        vm.warp(ts + oracle.MAX_STALENESS());
        assertEq(oracle.getPrice(), EXPECTED_6DEC);
    }

    // ─── Other funds-safety guards ───────────────────────────────────

    function test_feed_negative_answer_reverts() public {
        vm.prank(owner);
        oracle.setPriceFeed(address(feed));
        feed.setAnswer(-1);
        vm.expectRevert(abi.encodeWithSelector(PriceOracle.NegativePrice.selector, int256(-1)));
        oracle.getPrice();
    }

    function test_feed_zero_answer_reverts() public {
        vm.prank(owner);
        oracle.setPriceFeed(address(feed));
        feed.setAnswer(0);
        vm.expectRevert(abi.encodeWithSelector(PriceOracle.NegativePrice.selector, int256(0)));
        oracle.getPrice();
    }

    function test_feed_incomplete_round_reverts() public {
        vm.prank(owner);
        oracle.setPriceFeed(address(feed));
        feed.setUpdatedAt(0); // round not yet answered
        vm.expectRevert(PriceOracle.IncompleteRound.selector);
        oracle.getPrice();
    }

    function test_feed_carried_over_round_reverts() public {
        vm.prank(owner);
        oracle.setPriceFeed(address(feed));
        // answeredInRound < roundId → answer carried over from a prior round.
        feed.setRound(5, 4);
        vm.expectRevert(abi.encodeWithSelector(PriceOracle.StaleFeedRound.selector, uint80(5), uint80(4)));
        oracle.getPrice();
    }

    // ─── setPriceFeed access + validation ────────────────────────────

    function test_setPriceFeed_emits_event() public {
        vm.expectEmit(false, false, false, true);
        emit PriceOracle.PriceFeedChanged(address(0), address(feed));
        vm.prank(owner);
        oracle.setPriceFeed(address(feed));
    }

    function test_revert_setPriceFeed_non_owner() public {
        vm.prank(alice);
        vm.expectRevert(); // Ownable: OwnableUnauthorizedAccount
        oracle.setPriceFeed(address(feed));
    }

    function test_revert_setPriceFeed_decimals_too_large() public {
        MockAggregator badFeed = new MockAggregator(37, 1, block.timestamp);
        vm.expectRevert(abi.encodeWithSelector(PriceOracle.InvalidFeedDecimals.selector, uint8(37)));
        vm.prank(owner);
        oracle.setPriceFeed(address(badFeed));
    }

    function test_setPriceFeed_decimals_at_bound_allowed() public {
        // 36 decimals is the inclusive upper bound — accepted at config time.
        MockAggregator boundFeed = new MockAggregator(36, 1, block.timestamp);
        vm.prank(owner);
        oracle.setPriceFeed(address(boundFeed));
        assertEq(address(oracle.priceFeed()), address(boundFeed));
    }
}
