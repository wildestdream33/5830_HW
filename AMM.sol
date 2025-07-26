// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract AMM is AccessControl {
    bytes32 public constant LP_ROLE = keccak256("LP_ROLE");
    uint256 public invariant;
    address public tokenA;
    address public tokenB;
    uint256 feebps = 3; // fee in basis points

    event Swap(address indexed _inToken, address indexed _outToken, uint256 inAmt, uint256 outAmt);
    event LiquidityProvision(address indexed _from, uint256 AQty, uint256 BQty);
    event Withdrawal(address indexed _from, address indexed recipient, uint256 AQty, uint256 BQty);

    constructor(address _tokenA, address _tokenB) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(LP_ROLE, msg.sender);
        require(_tokenA != address(0) && _tokenB != address(0), "Token address cannot be 0");
        require(_tokenA != _tokenB, "Tokens cannot be the same");
        tokenA = _tokenA;
        tokenB = _tokenB;
    }

    function getTokenAddress(uint256 index) public view returns(address) {
        require(index < 2, "Only two tokens");
        return (index == 0) ? tokenA : tokenB;
    }

    function tradeTokens(address sellToken, uint256 sellAmount) public {
        require(invariant > 0, "Invariant must be nonzero");
        require(sellToken == tokenA || sellToken == tokenB, "Invalid token");
        require(sellAmount > 0, "Cannot trade 0");

        address buyToken = (sellToken == tokenA) ? tokenB : tokenA;

        // 1) read reserves before pulling in the new tokens
        uint256 reserveIn  = ERC20(sellToken).balanceOf(address(this));
        uint256 reserveOut = ERC20(buyToken).balanceOf(address(this));

        // 2) pull in full sellAmount (fee stays in the pool)
        ERC20(sellToken).transferFrom(msg.sender, address(this), sellAmount);

        // 3) apply fee and compute amountOut via Uniswap‐style formula:
        //    amountInWithFee = sellAmount * (10000 - feebps)
        //    outAmt = (amountInWithFee * reserveOut) / (reserveIn*10000 + amountInWithFee)
        uint256 amountInWithFee = sellAmount * (10000 - feebps);
        uint256 numerator        = amountInWithFee * reserveOut;
        uint256 denominator      = reserveIn * 10000 + amountInWithFee;
        uint256 outAmt           = numerator / denominator;

        require(outAmt > 0, "Bad trade");

        // 4) send output tokens
        ERC20(buyToken).transfer(msg.sender, outAmt);

        emit Swap(sellToken, buyToken, sellAmount, outAmt);

        // 5) update invariant to the new product (fees increase it)
        invariant = ERC20(tokenA).balanceOf(address(this))
                  * ERC20(tokenB).balanceOf(address(this));
    }

    function provideLiquidity(uint256 amtA, uint256 amtB) public {
        require(amtA > 0 || amtB > 0, "Cannot provide 0 liquidity");
        ERC20(tokenA).transferFrom(msg.sender, address(this), amtA);
        ERC20(tokenB).transferFrom(msg.sender, address(this), amtB);
        invariant = ERC20(tokenA).balanceOf(address(this))
                  * ERC20(tokenB).balanceOf(address(this));
        emit LiquidityProvision(msg.sender, amtA, amtB);
    }

    function withdrawLiquidity(address recipient, uint256 amtA, uint256 amtB)
        public onlyRole(LP_ROLE)
    {
        require(amtA > 0 || amtB > 0, "Cannot withdraw 0");
        require(recipient != address(0), "Cannot withdraw to 0 address");
        if (amtA > 0) ERC20(tokenA).transfer(recipient, amtA);
        if (amtB > 0) ERC20(tokenB).transfer(recipient, amtB);
        invariant = ERC20(tokenA).balanceOf(address(this))
                  * ERC20(tokenB).balanceOf(address(this));
        emit Withdrawal(msg.sender, recipient, amtA, amtB);
    }
}



