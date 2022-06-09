pragma solidity 0.8.14;

/**
making the neccesary imports and interfaces
**/

contract Arbitrage {

    address public owner;
    address[] private tos;
    bytes[] private data;

    modifier onlyOwner { 
        require(msg.sender == owner, "Sender is not owner of contract"); 
        _; 
    }

    constructor() {
        owner = msg.sender;
    }


    function changeOwner(address newOwner) onlyOwner() {
        owner = newOwner;
    }

    function approveTokens(address[] tokens, address[] lps) {

    }

    function getLoan() {

    }

    function Arb(address[] memory tos, bytes[] memory data) external payable onlyOwner() {
        require(tos.length > 0 && tos.length == data.length, "Invalid input");


        for(uint256 i; i < tos.length; i++) {
            (bool success,bytes memory returndata) = tos[i].call{value: address(this).balance, gas: gasleft()}(data[i]);
            
            require(success, string(returndata));
    }

    receive() payable external {}

    function transferTokens(address tokenAddress, address to, uint amount) external onlyOwner() {
        IERC20 token = IERC20(tokenAddress);
        token.transfer(to, amount);
    }

    /**
    function to add the dodo flash loan callback functions
    **/

}