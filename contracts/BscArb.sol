// SPDX-License-Identifier: UNLICENSED

pragma solidity ^0.8.0;


import "./ArbV1.sol";

contract BscArb is ArbV1 {
    function pancakeCall (address sender, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        (address[] memory addresses, bytes[] memory Data, address pairAddress,
            address factory, address initiator, uint amount,uint fee) = unpack(data);

        require(msg.sender == pairAddress,"Forbidden Caller");
        require(IFactory(factory).getPair(token,addresses[0]) == msg.sender, "Forbidden Caller");
        execute(sender,addresses,Data,initiator,amount,fee);
    }

    function swapV2Call (address sender, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        (address[] memory addresses, bytes[] memory Data, address pairAddress,
            address factory, address initiator, uint amount,uint fee) = unpack(data);

        require(msg.sender == pairAddress,"Forbidden Caller");
        require(IFactory(factory).getPair(token,addresses[0]) == msg.sender, "Forbidden Caller");
        execute(sender,addresses,Data,initiator,amount,fee);
    }

    function BiswapCall(address sender, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        (address[] memory addresses, bytes[] memory Data, address pairAddress,
            address factory, address initiator, uint amount,uint fee) = unpack(data);

        require(msg.sender == pairAddress,"Forbidden Caller");
        require(IFactory(factory).getPair(token,addresses[0]) == msg.sender, "Forbidden Caller");
        execute(sender,addresses,Data,initiator,amount,fee);
    }

    function babyCall (address sender, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        (address[] memory addresses, bytes[] memory Data, address pairAddress,
            address factory, address initiator, uint amount,uint fee) = unpack(data);

        require(msg.sender == pairAddress,"Forbidden Caller");
        require(IFactory(factory).getPair(token,addresses[0]) == msg.sender, "Forbidden Caller");
        execute(sender,addresses,Data,initiator,amount,fee);
    }

    function apeCall(address sender, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        (address[] memory addresses, bytes[] memory Data, address pairAddress,
            address factory, address initiator, uint amount,uint fee) = unpack(data);

        require(msg.sender == pairAddress,"Forbidden Caller");
        require(IFactory(factory).getPair(token,addresses[0]) == msg.sender, "Forbidden Caller");
        execute(sender,addresses,Data,initiator,amount,fee);
    }

    function uniswapV2Call(address sender, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        (address[] memory addresses, bytes[] memory Data, address pairAddress,
            address factory, address initiator, uint amount,uint fee) = unpack(data);

        require(msg.sender == pairAddress,"Forbidden Caller");
        require(IFactory(factory).getPair(token,addresses[0]) == msg.sender, "Forbidden Caller");
        execute(sender,addresses,Data,initiator,amount,fee);
    }

}