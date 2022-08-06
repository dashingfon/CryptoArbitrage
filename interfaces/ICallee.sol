// SPDX-License-Identifier: unlicence

pragma solidity ^0.8.0;

interface ICallee {

    function Call (address sender, uint amount0, uint amount1, bytes calldata data) external;

}