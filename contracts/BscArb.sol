// SPDX-License-Identifier: UNLICENSED

pragma solidity ^0.8.0;

import "./ArbV1.sol";

contract BscArb is ArbV1 {
    function pancakeCall (address /*sender*/, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        _respond(data);
    }

    function swapV2Call (address /*sender*/, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        _respond(data);
    }

    function BiswapCall (address /*sender*/, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        _respond(data);
    }

    function babyCall (address /*sender*/, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        _respond(data);
    }

    function apeCall (address /*sender*/, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        _respond(data);
    }

    function uniswapV2Call (address /*sender*/, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        _respond(data);
    }

    function fstswapCall (address /*sender*/, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        _respond(data);
    }

    function SwapCall (address /*sender*/, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        _respond(data);
    }

    function safeswapCall (address /*sender*/, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        _respond(data);
    }

    function nomiswapCall (address /*sender*/, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        _respond(data);
    }

    function jetswapCall (address /*sender*/, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        _respond(data);
    }
}