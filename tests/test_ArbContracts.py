import sys, os
sys.path.insert(1,
    os.path.join(os.path.split(os.path.dirname(__file__))[0],'scripts'))

import brownie, pytest
from brownie import accounts, Token, TestArb
from eth_abi import encode_abi
from web3 import Web3

@pytest.fixture(scope = 'module')
def Arb():
    return TestArb.deploy({'from': accounts[0]})

@pytest.fixture(scope = 'module')
def deployToken():
    return Token.deploy('Test Token','TST',{'from':accounts[0]})



class TestTransferAndRecieve():
    
    def test_recieveToken(self,deployToken,Arb):
        amount = 2e10
        print(Arb)
        r = Arb.address
        print(r)
        prevBal = deployToken.balanceOf(Arb)
        deployToken.transfer(Arb,amount,{'from' : accounts[0]})

        assert deployToken.balanceOf(Arb) == amount + prevBal

    def test_recieveNativeToken(self,Arb):
        amount = 2e10
        prevBal = Arb.balance()
        accounts[0].transfer(Arb,amount)

        assert Arb.balance() == amount + prevBal

    def test_transferTokenOwner(self,deployToken,Arb):
        amount = 1e10
        prevBal = deployToken.balanceOf(Arb)
        Arb.sendToken(deployToken,accounts[0],amount,{'from' : accounts[0]})

        assert deployToken.balanceOf(Arb) == prevBal - amount

    def test_transferTokenNotOwner(self,deployToken,Arb):
        with brownie.reverts():
            amount = 1e10
            Arb.sendToken(deployToken.address,accounts[0].address,amount,{'from' : accounts[1]} )

    def test_transferNativeTokenOwner(self,Arb):
        amount = 1e10
        prevBal = accounts[0].balance()
        Arb.sendCoin(accounts[0],amount,{'from' : accounts[0]})

        assert accounts[0].balance() == prevBal + amount
    
    def test_transferNativeTokenNotOwner(self,Arb):
        with brownie.reverts():
            amount = 1e10
            Arb.sendCoin(accounts[0],amount,{'from' : accounts[1]})

def test_unpack(Arb):
        addresses = ['0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c','0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c']
        data = [b'0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c',b'0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c']
        pairAddress = '0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c'
        factory = '0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c'
        initiator = '0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c'
        fee = 100301
        amount = 500

        defs = ['address[]','bytes[]','address','address','address','uint256','uint256']
        args = [addresses,data,pairAddress,factory,initiator,fee,amount]
        encoded = Web3.toHex(encode_abi(defs,args))
        
        result = Arb.pack(addresses,data,pairAddress,factory,initiator,fee,amount)

        assert encoded == result

class TestChange():
    def test_changeOwner(self,Arb):
        testOwner = accounts[1].address
        Arb.changeOwner(testOwner,{'from' : accounts[0]})

        assert Arb.retrieveOwner() == testOwner

    def test_changeOwnerNotOwner(self,Arb):
        with brownie.reverts():
            testOwner = '0xc087c78abac4a0e900a327444193dbf9ba69058e'
            Arb.changeOwner(testOwner,{'from' : accounts[0]})

    def test_changeCashoutOwner(self,Arb):
        test = True
        Arb.changeCashout(test,{'from' : accounts[1]})

        assert Arb.retrieveCashout()

    def test_changeCashoutNotOwner(self,Arb):
        with brownie.reverts():
            test = 1
            Arb.changeCashout(test,{'from' : accounts[0]})
