// SPDX-License-Identifier: UNLICENSED

pragma solidity ^0.8.0;

import '../interfaces/IFactory.sol';
import '../interfaces/IPair.sol';
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";


contract ArbV1 {
    
    using SafeMath for uint;

    bytes4 constant swapFuncSelector = bytes4(keccak256(bytes('swapExactTokensForTokens(uint256,uint256,address[],address,uint256)')));
    bytes4 constant approveFuncSelector = bytes4(keccak256(bytes('approve(address,uint256)')));

    address public owner;
    address internal token;
    bool internal instantCashout;

    event arbSuccesful (uint Gain, address Token, address initiator);
    event transferSent (address Token, address to);
    event CaleeResponse (uint amount, address exchange);

    modifier OnlyOwner() {
        require(owner == msg.sender);
        _;
    }

    constructor () {
        owner = msg.sender;
        instantCashout = true;
    }

    function start (
        uint amount0,
        uint amount1,
        address _token,
        bytes memory data) public {
            ( , , address tokensPair, , ) = unpack(data);

            require(_token == IPair(tokensPair).token0() || _token == IPair(tokensPair).token1(), 
                "Incorrect Pair for token");

            token = _token;
            IPair(tokensPair).swap(amount0,amount1,address(this),data);
        }

    function unpack (bytes memory data) public pure returns (
        address[] memory routers, bytes[] memory bytesList,
        address pairAddress,uint amount,uint fee) {
            
        (routers, bytesList, pairAddress, amount, fee) = abi.decode(
            data, (address[],bytes[],address,uint,uint));
    }


    function _execute (address[] memory routers, bytes[] memory data, uint amount, uint fee) private {
        
        uint256 swapAmount;
        address[] memory path;
        bool success;

        require(routers.length == data.length,"incongruent arrays!");
        emit CaleeResponse(amount, msg.sender);

        for (uint i; i < routers.length; i++) {
            path = abi.decode(data[i],(address[]));
            swapAmount = IERC20(path[0]).balanceOf(address(this));
            (success,) = path[0].call(abi.encodeWithSelector(approveFuncSelector,routers[i],swapAmount));
            require(success,"Failed to approve");

            (success,) = routers[i].call(abi.encodeWithSelector(
                swapFuncSelector, swapAmount,0,path,address(this),block.timestamp + 60));
            require(success,"Failed to swap");
        }

        uint amountGot = IERC20(token).balanceOf(address(this));
        uint amountExpected = amount.mul(fee).div(100000);
        require (amountGot > amountExpected,"Unsuccesful Arb!");
        uint gain = amountGot.sub(amountExpected);
        emit arbSuccesful(gain,token,tx.origin);
        
        _sendToken(token, msg.sender, amountExpected);

        if (instantCashout) {
            _sendToken(token, tx.origin, gain);
        } else {
            _sendToken(token, owner, gain);
        }
    }

    function _respond(bytes calldata data) internal {
        (address[] memory addresses, bytes[] memory Data, address pairAddress, uint amount, uint fee) = unpack(data);

        require(msg.sender == pairAddress,"Forbidden Caller");
        _execute(addresses,Data,amount,fee);
    }

    function _sendCoin(address payable recipient, uint amount) private {
        (bool sent, ) = recipient.call{value: amount}("");
        require(sent, "Failed to send Ether");
        emit transferSent(address(0),recipient);
    }
    
    function sendCoin(address payable recipient, uint amount) external OnlyOwner() {
        _sendCoin(recipient,amount);
    }

    function _sendToken(address tokenAdd, address reciepient, uint amount) private {
        require(IERC20(tokenAdd).balanceOf(address(this)) >= amount,"Insufficient Funds");
        IERC20(tokenAdd).transfer(reciepient, amount);
        emit transferSent(tokenAdd, reciepient);
    }
    function sendToken(address tokenAdd, address reciepient,uint amount) external OnlyOwner() {
        _sendToken(tokenAdd,reciepient,amount);
    }

    function changeOwner (address _owner) external OnlyOwner() {
        owner = _owner;
    }

    function changeCashout (bool _method) external OnlyOwner() {
        instantCashout = _method;
        
    }
    function skim(address skimPair) external {
        IPair(skimPair).skim(msg.sender);
    }

    receive() external payable {}
}

