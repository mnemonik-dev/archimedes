// SPDX-License-Identifier: Unlicense
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import "./interfaces/ISyntheticFactory.sol";
import "./PriceOracle.sol";
import "./SyntheticToken.sol";
import "./SyntheticVault.sol";

/// @title SyntheticFactory
/// @notice Creates and manages synthetic assets backed by USDC collateral.
///         One call deploys PriceOracle + SyntheticToken + SyntheticVault.
///         Users mint/redeem directly with each per-asset SyntheticVault.
///         Hackathon: 120% collateral ratio (default), no liquidation engine.
contract SyntheticFactory is ISyntheticFactory, Ownable {
    // ─── State ───────────────────────────────────────────────────────

    address public immutable override usdc;

    mapping(address => bool) private _registered;
    address[] private _syntheticList;

    mapping(address => address) public tokenOracle;
    mapping(address => address) public tokenVault;

    // ─── Constructor ─────────────────────────────────────────────────

    constructor(address _usdc, address _owner) Ownable(_owner) {
        usdc = _usdc;
    }

    // ─── Admin ───────────────────────────────────────────────────────

    /// @notice Deploy a new synthetic asset in one call.
    ///         Creates oracle → token → vault, wires them together.
    ///         Caller should set oracle price separately after creation.
    function createSynthetic(
        string calldata name,
        string calldata symbol,
        address oracle
    ) external override onlyOwner returns (address token) {
        SyntheticToken synthToken = new SyntheticToken(name, symbol, owner());
        token = address(synthToken);

        SyntheticVault vault = new SyntheticVault(
            address(usdc),
            token,
            oracle,
            owner()
        );

        synthToken.setVault(address(vault));

        _registered[token] = true;
        _syntheticList.push(token);
        tokenOracle[token] = oracle;
        tokenVault[token] = address(vault);

        emit SyntheticCreated(token, symbol, oracle);
    }

    // ─── Mint / Redeem ───────────────────────────────────────────────
    // Users interact directly with the per-asset SyntheticVault.
    // These are view-only convenience functions that route to the correct vault.

    function mint(address synthetic, uint256 usdcAmount)
        external
        override
        returns (uint256 synthAmount)
    {
        // Route to the per-asset vault
        // User must approve the vault (not this factory) for USDC
        address vault = tokenVault[synthetic];
        require(vault != address(0), "Not registered");

        // The vault handles everything — just call it
        // Note: user must have approved the vault directly
        synthAmount = SyntheticVault(payable(vault)).mint(usdcAmount);
    }

    function redeem(address synthetic, uint256 synthAmount)
        external
        override
        returns (uint256 usdcAmount)
    {
        address vault = tokenVault[synthetic];
        require(vault != address(0), "Not registered");

        // Note: user must have approved the vault for synth tokens (if needed)
        usdcAmount = SyntheticVault(payable(vault)).burn(synthAmount);
    }

    // ─── Views ───────────────────────────────────────────────────────

    function getPrice(address synthetic) external view override returns (uint256 price) {
        address oracle = tokenOracle[synthetic];
        require(oracle != address(0), "Not registered");
        return PriceOracle(oracle).getPrice();
    }

    function totalCollateral() external view override returns (uint256) {
        // Sum USDC across all per-asset vaults
        uint256 total;
        for (uint256 i = 0; i < _syntheticList.length; i++) {
            total += IERC20(usdc).balanceOf(tokenVault[_syntheticList[i]]);
        }
        return total;
    }

    function totalSynthValue() external view override returns (uint256) {
        uint256 total;
        for (uint256 i = 0; i < _syntheticList.length; i++) {
            address token = _syntheticList[i];
            uint256 supply = SyntheticToken(token).totalSupply();
            if (supply > 0) {
                uint256 price = PriceOracle(tokenOracle[token]).getPrice();
                total += (supply * price) / 1e18;
            }
        }
        return total;
    }

    function healthRatio() external view override returns (uint256) {
        uint256 synthVal = this.totalSynthValue();
        if (synthVal == 0) return 1e18;
        return (this.totalCollateral() * 1e18) / synthVal;
    }

    function getSynthetics() external view override returns (address[] memory) {
        return _syntheticList;
    }
}
