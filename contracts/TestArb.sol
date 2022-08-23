// SPDX-License-Identifier: UNLICENSED

pragma solidity ^0.8.0;

import "./ArbV1.sol";

contract TestArb is ArbV1 {
    function getSelector(string calldata func) external pure returns (bytes4) {
        return bytes4(keccak256(bytes(func)));
    }

    function Call (address /*sender*/, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {
        _respond(data);
    }
    function retrieveOwner() external view returns(address) {
        return owner;
    }
    function retrieveCashout() external view returns(bool) {
        return instantCashout;
    }
    function pack(
        address[] memory addresses,
        bytes[] memory data,
        address pairAddress,
        uint amount) external pure returns(bytes memory) {
            return abi.encode(addresses,data,pairAddress,amount);
    }
}
