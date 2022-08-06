import sys, os

sys.path.insert(1,
    os.path.join(os.path.split(os.path.dirname(__file__))[0],'scripts'))

import pytest
import Blockchains as Blc
import Controller as Ctr
import Config as Cfg
from eth_abi import encode_abi
from brownie import accounts, Token, Factory, Router,TestArb
from web3 import Web3
from datetime import datetime, timedelta


CtrSetup = Ctr.Controller(Blc.Kovan())

@pytest.fixture(scope = 'module')
def Contract():
    return TestArb.deploy({'from' : accounts[0]})


def deployTokens(details):
    for i in details:
        Token.deploy(*i,{'from':accounts[0]})

def deployFactory():
    Factory.deploy('0x0000000000000000000000000000000000000000',{'from':accounts[0]})
    
def deployRouter(factory):
    Router.deploy(factory,{'from':accounts[0]})
    
def createPairsAndAddLiquidity(R,details):
    verdict = True
    for i in details:
        amount1, amount2 = R.addLiquidity(*i,{'from':accounts[0]})
        verdict = i[2],i[3] ==  amount1,amount2
        if not verdict:
            break
    
    return verdict


@pytest.fixture(scope = 'module')
def setupEnvironment(Contract):
    '''
    deploy the tokens
    deploy the factory
    deploy the router
    create the pairs and add liquidity    
    '''
    tokenDetails = [
        ['Test Token 1','TST1',],
        ['Test Token 2','TST2',],
        ['Test Token 3','TST3',],
        ['Test Token 4','TST4',],
    ]
    deployTokens(tokenDetails)
    deployFactory()
    deployRouter(Factory[0].address)
   
    pairDetails = [
        [Token[0].address,Token[1].address,70e18,65e18,70e18,65e18,Contract.address,int((datetime.now() + timedelta(seconds= 60)).timestamp())],
        [Token[0].address,Token[2].address,50e18,67e18,50e18,67e18,Contract.address,int((datetime.now() + timedelta(seconds= 60)).timestamp())],
        [Token[1].address,Token[2].address,47e18,100e18,47e18,100e18,Contract.address,int((datetime.now() + timedelta(seconds= 60)).timestamp())],
        
    ]
    verdict = createPairsAndAddLiquidity(Router[0],pairDetails)
    
    return verdict


def equal(list1,list2):
    list_dif = [i for i in list1 + list2 if i not in list1 or i not in list2]
    return False if list_dif else True



ROUTES = [
    {
        'route' : [{'from': 'TST1', 'to': 'TST2', 'via': 'fonswap'}, {'from': 'TST2', 'to': 'TST3', 'via': 'fonswap'}, {'from': 'TST3', 'to': 'TST1', 'via': 'fonswap'}],
        'simplified' : 'TST1 TST2 fonswap - TST2 TST3 fonswap - TST3 TST1 fonswap',
        'EP' : 0.30412659013303345,
        'capital' : 0.1919007137570744
    },
    {
        'route' : [{'from': 'TST2', 'to': 'TST1', 'via': 'fonswap'}, {'from': 'TST1', 'to': 'TST3', 'via': 'fonswap'}, {'from': 'TST3', 'to': 'TST2', 'via': 'fonswap'}],
        'simplified' : 'TST2 TST1 fonswap - TST1 TST3 fonswap - TST3 TST2 fonswap',
    },
    {
        'route' : [{'from': 'TST3', 'to': 'TST1', 'via': 'fonswap'}, {'from': 'TST1', 'to': 'TST2', 'via': 'fonswap'}, {'from': 'TST2', 'to': 'TST3', 'via': 'fonswap'}],
        'simplified' : 'TST3 TST1 fonswap - TST1 TST2 fonswap - TST2 TST3 fonswap',
    },
]

class TestGetRoutes():
    def test_getRoutes(self):
        routes = list(CtrSetup.getRoutes(arbRoute = True))
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
        else:
            assert sortedAdds == (address1,address2)
    
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

def test_getAmountsOut(setupEnvironment):
    assert setupEnvironment

    amount, addresses = 0.5e18, [Token[0].address,Token[1].address,Token[2].address]
    expected = Router[0].getAmountsOut(amount,addresses)[-1]

    assert CtrSetup.getAmountsOut(Router[0],amount,addresses) == expected


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
            'amount0' : int(0.14507823882784862e18),
            'amount1' : 0,
            'pair' : '0xe3520349f477a5f6eb06107066048508498a291b',
            'factory' : '0xc9bdeed33cd01541e1eed10f90519d2c06fe3feb',
            'routers' : ['0xf4eb217ba2454613b15dbdea6e5f22276410e89e',
        '0xf4eb217ba2454613b15dbdea6e5f22276410e89e',
        '0xf4eb217ba2454613b15dbdea6e5f22276410e89e',
        '0xf4eb217ba2454613b15dbdea6e5f22276410e89e'],
            'fee' : 100301,
            'timeStamp' : False,
            'Outs' : [1.3227394770402876,1.218499093584138,1.6198156380906548,3.4190331223878387],
            'contract' : '0x249cd054697f41d73f1a81fa0f5279fcce3cf70c',}
        
        values = CtrSetup.getValues(ITEMS[0],OPTIONS[0])

        assert result == values

    @pytest.mark.parametrize('options,item,prepared',PACKAGES)
    def test_payloadResult(self,options,item,prepared):
        payload = CtrSetup.prepPayload(item = item, options = options)
        assert payload == prepared


@pytest.fixture(scope = 'module')
def MAIN_OPTION(): 
    return {'tokens' : {'TST1' : Token[0].address,'TST2' : Token[1].address, 'TST3' : Token[2].address, 'TST4' : Token[3].address},
        'pair' : Factory[0].getPair(Token[0].address,Token[1].address),
        'factory' : Factory[0].address,
        'routers' : [Router[0].address,Router[0].address,Router[0].address],
        'fee' : 100301,
        'timeStamp' : False}

class TestExecution():
    def correctBalance(self,contract,balance, token):
        if token.balanceOf(contract) >= balance:
            return True
        else:
            return False

    def test_arb(self,setupEnvironment,Contract,MAIN_OPTION):
        assert setupEnvironment
        
        CtrSetup.arb(routes = [ITEMS[0]],keyargs = [MAIN_OPTION])
        assert self.correctBalance(Contract,0.30412e18,Token[0])

    
