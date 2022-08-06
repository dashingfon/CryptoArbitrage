// SPDX-License-Identifier: UNLICENSED

pragma solidity ^0.8.0;



import '../interfaces/IFactory.sol';
import '../interfaces/IPair.sol';
import './Pair.sol';


contract Factory is IFactory {
    address public feeTo;
    address public feeToSetter;
    bytes32 public constant INIT_CODE = keccak256(abi.encodePacked(type(Pair).creationCode));

    mapping(address => mapping(address => address)) public Pairs;
    address[] public pairsList;

    constructor(address _feeToSetter) {
        feeToSetter = _feeToSetter;
    }

    function INIT_CODE_HASH() external pure returns (bytes32) {
        return INIT_CODE;
    }
    function getPair (address tokenA, address tokenB) external view returns (address pair) {
        pair = Pairs[tokenA][tokenB];
    }

    function allPairs (uint index) external view returns (address pair) {
        pair = pairsList[index];
    }

    function allPairsLength() external view returns (uint) {
        return pairsList.length;
    }

    function createPair(address tokenA, address tokenB) external returns (address pair) {
        require(tokenA != tokenB, 'UniswapV2: IDENTICAL_ADDRESSES');
        (address token0, address token1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);
        require(token0 != address(0), 'UniswapV2: ZERO_ADDRESS');
        require(Pairs[token0][token1] == address(0), 'UniswapV2: PAIR_EXISTS'); // single check is sufficient
        bytes memory bytecode = type(Pair).creationCode;
        bytes32 salt = keccak256(abi.encodePacked(token0, token1));
        assembly {
            pair := create2(0, add(bytecode, 0x20), mload(bytecode), salt)
        }
        IPair(pair).initialize(token0, token1);
        Pairs[token0][token1] = pair;
        Pairs[token1][token0] = pair; // populate mapping in the reverse direction
        pairsList.push(pair);
        emit PairCreated(token0, token1, pair, pairsList.length);
    }

    function setFeeTo(address _feeTo) external {
        require(msg.sender == feeToSetter, 'UniswapV2: FORBIDDEN');
        feeTo = _feeTo;
    }


    function setFeeToSetter(address _feeToSetter) external {
        require(msg.sender == feeToSetter, 'UniswapV2: FORBIDDEN');
        feeToSetter = _feeToSetter;
    }
}