import sys, os
sys.path.insert(1,
    os.path.join(os.path.split(os.path.dirname(__file__))[0],'scripts'))

import pytest
import Blockchains as Blc
import Controller as Ctr
import Config as Cfg
from eth_abi import encode_abi
from brownie import accounts, Token, Factory, Router, TestArb, interface
from web3 import Web3
from datetime import datetime, timedelta


CtrSetup = Ctr.Controller(Blc.Kovan())

@pytest.fixture(scope = 'module')
def Contract():
    Cont = TestArb.deploy({'from' : accounts[0]})
    CtrSetup.contractAddress = Cont.address
    return Cont


def deployTokens(details):
    print(f'Test Tokens addresses')
    for index, i in enumerate(details):
        T = Token.deploy(*i,{'from':accounts[0]})
        print(f'Token {index} address :- {T.address}')

def deployFactory():
    F = Factory.deploy('0x0000000000000000000000000000000000000000',{'from':accounts[0]})
    #print(f'Factory address :- {F.address}')


def deployRouter(factory):
    R = Router.deploy(factory,{'from':accounts[0]})
    print(f'Router address :- {R.address}')

def approve(token, amount, address):
    tx = token.approve(address,amount,{'from' : accounts[0]})
    tx.wait(1)

def createPairsAndAddLiquidity(R,details):
    print(f'Test Pairs addresses')
    for index, i in enumerate(details):
        approve(i[0],i[2],R.address)
        approve(i[1],i[3],R.address)
        content = [i[0].address,i[1].address] + i[2:]
        liq = R.addLiquidity(*content,{'from':accounts[0]})
        liq.wait(1)

        print(f'Pair {index} address :-')
        pair = Factory[0].getPair(i[0].address,i[1].address)
        print(pair)
        print(f'Pair {index} reserves :-')
        reserve0, reserve1, _ = interface.IPair(pair).getReserves()
        print(f'reserve0 :- {reserve0}, reserve1 :- {reserve1}')


TOKEN_DETAILS = [
        ['Test Token 1','TST1',],
        ['Test Token 2','TST2',],
        ['Test Token 3','TST3',],
        ['Test Token 4','TST4',],
    ]


def equal(list1,list2):
    list_dif = [i for i in list1 + list2 if i not in list1 or i not in list2]
    return False if list_dif else True



ROUTES = [
    {
        'route' : [{'from': 'TST1', 'to': 'TST2', 'via': 'fonswap'}, {'from': 'TST2', 'to': 'TST3', 'via': 'fonswap'}, {'from': 'TST3', 'to': 'TST1', 'via': 'fonswap'}],
        'simplified' : 'TST1 TST2 fonswap - TST2 TST3 fonswap - TST3 TST1 fonswap',
        'EP' : 0.30412659013303345,
        'capital' : 0.1919007137570744
    }
]

class TestGetRoutes():
    def test_getRoutes(self):
        routes = list(CtrSetup.getRoutes())
        print(routes)
        assert equal(ROUTES,routes)

def test_getProspect():
    prospects = list(CtrSetup.getProspect(ROUTES))
    ans = [{
        'route' : [{'from': 'TST1', 'to': 'TST2', 'via': 'fonswap'}, {'from': 'TST2', 'to': 'TST3', 'via': 'fonswap'}, {'from': 'TST3', 'to': 'TST1', 'via': 'fonswap'}],
        'simplified' : 'TST1 TST2 fonswap - TST2 TST3 fonswap - TST3 TST1 fonswap',
        'EP' : 0.30412659013303345e18,
        'capital' : 0.1919007137570744e18
    }]
    assert prospects == ans

def test_encodeCall():
    signature = 'testing'
    defs = ['string','uint256']
    args = ['testing',234545]

    data = signature + Web3.toHex(encode_abi(defs,args))[2:]
    assert data == CtrSetup.encodeCall(signature,defs,args)

class TestSortingAddresses():

    @pytest.mark.parametrize('address1,address2',[
        ('0xc42c30ac6cc15fac9bd938618bcaa1a1fae8501d',
        '0xb12bfca5a55806aaf64e99521918a4bf0fc40802'),
        ('0xe3520349f477a5f6eb06107066048508498a291b',
        '0xc9bdeed33cd01541e1eed10f90519d2c06fe3feb')])
    def test_sortAddresses(self,address1,address2):
        
        sortedAdds = CtrSetup.sortTokens(address1,address2)
        if str.encode(address1).hex() > str.encode(address2).hex():
            assert sortedAdds == (address2,address1)

        else: assert sortedAdds == (address1,address2)
    

    def test_invalidSort(self):
        with pytest.raises(ValueError):
            CtrSetup.sortTokens(
                '0xc42c30ac6cc15fac9bd938618bcaa1a1fae8501d',
                '0xc42c30ac6cc15fac9bd938618bcaa1a1fae8501d')

class TestSignatures():
    '''
    self.swapFuncSig = ' 0x38ed1739' #'swapExactTokensForTokens(uint256,uint256,address[],address,uint256)'
    self.approveFuncSig = '0x095ea7b3' #'approve(address,uint256)'''

    def test_swapSig(self,Contract):
        string = 'swapExactTokensForTokens(uint256,uint256,address[],address,uint256)'
        result = Contract.getSelector(string)

        assert result == CtrSetup.swapFuncSig

    def test_approveSig(self,Contract):
        string = 'approve(address,uint256)'
        result = Contract.getSelector(string)

        assert result == CtrSetup.approveFuncSig

def test_getAmountsOut(Contract):
    deployTokens(TOKEN_DETAILS)
    PAIR_DETAILS = [
    [Token[3],Token[1],60e18,80e18,60e18,80e18,Contract.address,int((datetime.now() + timedelta(seconds= 600)).timestamp())],
    [Token[1],Token[2],70e18,65e18,70e18,65e18,Contract.address,int((datetime.now() + timedelta(seconds= 600)).timestamp())],
    [Token[2],Token[0],50e18,67e18,50e18,67e18,Contract.address,int((datetime.now() + timedelta(seconds= 600)).timestamp())],
    [Token[0],Token[3],47e18,67e18,47e18,67e18,Contract.address,int((datetime.now() + timedelta(seconds= 600)).timestamp())],
    ]

    deployFactory()
    deployRouter(Factory[0].address)
    createPairsAndAddLiquidity(Router[0],PAIR_DETAILS)

    routerAddress = Router[0].address
    amount, addresses = int(0.02867159537482727e18), [Token[3].address,Token[1].address]
    expected = int(amount * 1.3280093080532045)

    assert CtrSetup.getAmountsOut(routerAddress,amount,addresses) >= expected

#0.03806087235484626
#assert 38095957533867248 == 38076145534505824

ITEMS = Cfg.ITEMS
OPTIONS = Cfg.OPTIONS
PACKAGES = Cfg.PACKAGES


class TestPayload():

    def test_getValues(self):
        result = {
            'tokens' : {
        'TST1' : '0xc42c30ac6cc15fac9bd938618bcaa1a1fae8501d',
        'TST2' : '0xb12bfca5a55806aaf64e99521918a4bf0fc40802', 
        'TST3' : '0x4988a896b1227218e4a686fde5eabdcabd91571f',
        'TST4' : '0x5ce9f0b6afb36135b5ddbf11705ceb65e634a9dc'},
            'names' : ('TST4','TST2'),
            'pair' : '0xe3520349f477a5f6eb06107066048508498a291b',
            'factory' : '0xc9bdeed33cd01541e1eed10f90519d2c06fe3feb',
            'routers' : ['0xf4eb217ba2454613b15dbdea6e5f22276410e89e',
        '0xf4eb217ba2454613b15dbdea6e5f22276410e89e',
        '0xf4eb217ba2454613b15dbdea6e5f22276410e89e',
        '0xf4eb217ba2454613b15dbdea6e5f22276410e89e'],
        'fee' : 100301}

        values = CtrSetup.getValues(ITEMS[0],OPTIONS[0])

        assert result == values

    @pytest.mark.parametrize('options,item,prepared',PACKAGES)
    def test_payloadResult(self,options,item,prepared):
        payload = CtrSetup.prepPayload(item = item, options = options)
        assert payload == prepared
 

def MAIN_OPTION(): 
    return {'tokens' : {'TST1' : Token[0].address,'TST2' : Token[1].address, 'TST3' : Token[2].address, 'TST4' : Token[3].address},
        'pair' : Factory[0].getPair(Token[3].address,Token[1].address),
        'factory' : Factory[0].address,
        'routers' : [Router[0].address,Router[0].address,Router[0].address,Router[0].address],
        'fee' : 100301,
        'out' : 1.3280093080532045
    }
    
def MAIN_ITEM(): 
    return [
    {
        'EP' : 0.02867159537482727 * (2.3274766143031744 - 1),
        'capital' : 0.02867159537482727,
        'simplified' : "TST4 TST2 fonswap - TST2 TST3 fonswap - TST3 TST1 fonswap - TST1 TST4 fonswap",
        'route' : [{'from': 'TST4', 'to': 'TST2', 'via': 'fonswap'}, {'from': 'TST2', 'to': 'TST3', 'via': 'fonswap'}, {'from': 'TST3', 'to': 'TST1', 'via': 'fonswap'},{'from': 'TST1', 'to': 'TST4', 'via': 'fonswap'}] ,
    }]

class TestExecution():
    def correctBalance(self,account,balance, token):
        if token.balanceOf(account) >= balance:
            return True
        else:
            return False

    
    def test_arb(self):

        option = MAIN_OPTION()
        item = MAIN_ITEM()
        
        CtrSetup.arb(routes = item,keyargs = [option])
        
        assert self.correctBalance(accounts[0].address,0.038060e18,Token[3])

    
