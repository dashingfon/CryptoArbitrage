// SPDX-License-Identifier: unlicence

pragma solidity ^0.8.0;


interface IFactory {
  event PairCreated(address indexed token0, address indexed token1, address pair, uint);

    function INIT_CODE_HASH() external pure returns (bytes32);
    function feeTo() external view returns (address);
    function feeToSetter() external view returns (address);

    function getPair(address tokenA, address tokenB) external view returns (address pair);
    function allPairs(uint) external view returns (address pair);
    function allPairsLength() external view returns (uint);

    function createPair(address tokenA, address tokenB) external returns (address pair);

    function setFeeTo(address) external;
    function setFeeToSetter(address) external;
    }