// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "openzeppelin-contracts/contracts/access/AccessControl.sol";
import "./BridgeToken.sol";
import "./interfaces/MToken.sol";

contract Destination is AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    mapping(MToken => BridgeToken) public wrapped_tokens;
    mapping(BridgeToken => MToken) public underlying_tokens;

    event Creation(MToken indexed underlying_token, BridgeToken indexed wrapped_token);
    event Wrap(MToken indexed underlying_token, BridgeToken indexed wrapped_token, address indexed to, uint256 amount);
    event Unwrap(MToken indexed underlying_token, BridgeToken indexed wrapped_token, address indexed from, address to, uint256 amount);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }

    function createToken(MToken mtoken, string memory name, string memory symbol) public onlyRole(ADMIN_ROLE) returns (BridgeToken) {
        BridgeToken token = new BridgeToken(name, symbol, address(this));
        token.grantRole(token.DEFAULT_ADMIN_ROLE(), address(this));
        token.grantRole(token.MINTER_ROLE(), address(this));

        wrapped_tokens[mtoken] = token;
        underlying_tokens[token] = mtoken;

        emit Creation(mtoken, token);
        return token;
    }

    function wrap(MToken mtoken, address to, uint256 amount) public {
        BridgeToken token = wrapped_tokens[mtoken];
        require(address(token) != address(0), "Destination: token not registered");

        token.mint(to, amount);
        emit Wrap(mtoken, token, to, amount);
    }

    function unwrap(BridgeToken token, address to, uint256 amount) public {
        MToken mtoken = underlying_tokens[token];
        require(address(mtoken) != address(0), "Destination: token not registered");

        token.burnFrom(msg.sender, amount);
        emit Unwrap(mtoken, token, msg.sender, to, amount);
    }
}





