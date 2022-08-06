// SPDX-License-Identifier: UNLICENSED

pragma solidity ^0.8.0;

import '../interfaces/IFactory.sol';
import '../interfaces/IPair.sol';
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";


contract ArbV1 {
    
    using SafeMath for uint;

    address public owner;
    address internal token;
    bool internal instantCashout;
    uint internal balance;

    event arbSuccesful (uint Gain, address Token, address initiator);
    event transferSent (address Token, address to);
    event CaleeResponse (uint amount, address exchange);

    modifier OnlyOwner () {
        require(owner == msg.sender);
        _;
    }

    constructor () {
        owner = msg.sender;
        instantCashout = false;
    }

    function start (
        uint amount0,
        uint amount1,
        address _token,
        bytes memory data) public {
            (, , address tokensPair, , , , ) = unpack(data);

            require(_token == IPair(tokensPair).token0() || _token == IPair(tokensPair).token1(), "Incorrect Pair for token");
            token = _token;
            balance = IERC20(token).balanceOf(address(this));
            IPair(tokensPair).swap(amount0,amount1,msg.sender,data);
        }

    function unpack (bytes memory data) public pure returns (
        address[] memory addresses,bytes[] memory dataAddrs,address pairAddress,
        address factory,address initiator,uint amount,uint fee) {
            
        (addresses, dataAddrs, pairAddress,factory,initiator,amount, fee) = abi.decode(
            data, (address[],bytes[],address,address,address,uint,uint));
    }


    function execute (address sender, address[] memory tokens, bytes[] memory data,
        address initiator,uint amount,uint fee) internal {
        require(tokens.length > 2 && tokens.length == data.length,"incongruent arrays!");
        
        emit CaleeResponse(amount, msg.sender);

        for (uint i; i < tokens.length; i++) {
            (bool success, ) = tokens[i].call(data[i]);
            require(success,"Failed to execute swap!");
        }

        uint amountGot = IERC20(token).balanceOf(address(this));
        uint amountExpected = balance.add(amount.mul(fee).div(100000));
        require (amountGot > amountExpected,"Unsuccesful Arb!");
        uint gain = amountGot - amountExpected;
        emit arbSuccesful(gain,token,initiator);
        
        _sendToken(token, msg.sender, amount.mul(fee).div(100000));

        if (instantCashout) {
            _sendToken(token,sender,gain);
        }
    }

    function _sendCoin(address payable recipient, uint amount) private {
        (bool sent, ) = recipient.call{value: amount}("");
        require(sent, "Failed to send Ether");
        emit transferSent(address(0),recipient);
    }


    function sendCoin(address payable recipient, uint amount) public OnlyOwner() {
        _sendCoin(recipient,amount);
    }

    function _sendToken(address tokenAdd, address reciepient, uint amount) private {
        require(IERC20(tokenAdd).balanceOf(address(this)).sub(amount) > 0,"Insufficient funds");
        IERC20(tokenAdd).transfer(reciepient, amount);
        emit transferSent(tokenAdd, reciepient);
    }
    function sendToken(address tokenAdd, address reciepient,uint amount) public OnlyOwner() {
        _sendToken(tokenAdd,reciepient,amount);
    }

    function changeOwner (address _owner) public OnlyOwner() {
        owner = _owner;
    }

    function changeCashout (bool _method) public OnlyOwner() {
        instantCashout = _method;
        
    }
    function skim(address skimPair) external {
        IPair(skimPair).skim(msg.sender);
    }

    receive() external payable {}
}

