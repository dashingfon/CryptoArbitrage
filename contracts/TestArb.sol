// SPDX-License-Identifier: UNLICENSED

pragma solidity ^0.8.0;

import "./ArbV1.sol";

contract TestArb is ArbV1 {
    function getSelector(string calldata function0) external pure returns (bytes4) {
        return bytes4(keccak256(bytes(function0)));
    }

    function Call (address sender, uint /*amount0*/, uint /*amount1*/, bytes calldata data) external {

        (address[] memory addresses, bytes[] memory Data, address pairAddress,
            address factory, address initiator, uint amount,uint fee) = unpack(data);

        require(msg.sender == pairAddress,"Forbidden Caller");
        require(IFactory(factory).getPair(token,addresses[0]) == msg.sender, "Forbidden Caller");
        execute(sender,addresses,Data,initiator,amount,fee);
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
        address factory,
        address initiator,
        uint fee,
        uint amount) external pure returns(bytes memory) {
            return abi.encode(addresses,data,pairAddress,factory,initiator, fee,amount);
    }
}
