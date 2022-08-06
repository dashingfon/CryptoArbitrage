'''from functools import wraps
import time
import dotenv
'''
from web3 import Web3
#import Controller as Ctr
#from ratelimit import limits, RateLimitException, sleep_and_retry

from pycoingecko import CoinGeckoAPI
#import os
import json
from eth_abi import encode_abi
import Blockchains as Blc



if __name__ == '__main__':


    #  Ratelimit module Usage

    '''

    AMOUNT = 1
    PERIOD = 1

    @sleep_and_retry
    @limits(calls = AMOUNT, period = PERIOD)
    def test(self):
        print('testing...')'''



    '''

    curr = os.path.dirname(__file__)
    parent = os.path.split(curr)[0]
    file = os.path.join(parent, 'Data', 'Aurora', 'arbRoute.json')
    print(file)
    '''


    class Test():
        def __init__(self):
            self.purpose = 'test'

        def __repr__(self):
            return 'Aurora Blockchain'

    def test():
        while True:
            yield 'yeah'

    def assemble(route):
            result = []
            routeList = route.split(' - ')
            for item in routeList:
                itemList = item.split()
                load = {
                    'from' : itemList[0],
                    'to' : itemList[1],
                    'via' : itemList[2],
                }
                result.append(load)
            return result

    def lookupPrice(self):
        def getPriceLookup():
            try:
                with open(self.priceLookupPath) as PP:
                    temp = json.load(PP)
            except FileNotFoundError:
                temp = {}
            
            return temp
        
        temp = getPriceLookup()

        Testnet = self.checkIfTestnet()
        prices = {}
        if not Testnet:

            tokenAdresses = []
            for i in self.tokens.values():
                tokenAdresses.append(i)

            Cg = CoinGeckoAPI()
            prices = Cg.get_token_price(
                id = self.coinGeckoId,
                contract_addresses = tokenAdresses,
                vs_currencies = 'usd' )
        
        with open(self.priceLookupPath,'w') as PW:
            json.dump({**temp,**prices},PW,indent = 2)


    #lookupPrice(Blc.BSC())


    test = Blc.Aurora()
    route = [
        {
        "from" : "TST4",
        "to" : "TST2",
        "via" : "fonswap"
        },
        {
        "from" : "TST2",
        "to" : "TST3",
        "via" : "fonswap"
        },
        {
            "from" : "TST3",
            "to" : "TST1",
            "via" : "fonswap"
        },
        {
            "from" : "TST1",
            "to" : "TST4",
            "via" : "fonswap"
        }
    ]

    prices = [
        {'TST4' : 60, 'TST2' : 80},
        {'TST2' : 70, 'TST3' : 65},
        {'TST3' : 50, 'TST1' : 67},
        {'TST1' : 47, 'TST4' : 100}
    ]


    '''print(test.pollRoute(route = route, prices = prices))
    print(test.assemble("TST4 TST2 fonswap - TST2 TST3 fonswap - TST3 TST1 fonswap - TST1 TST1 fonswap"))
    '''

    '''
    The getPayloadBytes function compiles the data as it would be calling prepPayload from the Controller class

    '''
    def getPayloadBytes(pos):
        assert 1 <= pos <= 4

        T1 = '0xc42c30ac6cc15fac9bd938618bcaa1a1fae8501d'
        T2 = '0xb12bfca5a55806aaf64e99521918a4bf0fc40802'
        T3 = '0x4988a896b1227218e4a686fde5eabdcabd91571f'
        T4 = '0x5ce9f0b6afb36135b5ddbf11705ceb65e634a9dc'

        fonswapRouter = '0xf4eb217ba2454613b15dbdea6e5f22276410e89e'
        dodoRouter = '0x04580ce6dee076354e96fed53cb839de9efb5f3f'

        contract = '0x249cd054697f41d73f1a81fa0f5279fcce3cf70c'

        def getApprove(address,amount,sig = '0x095ea7b3'):
            defs = ['address','uint256']
            args = [address,amount]
            byteData = encode_abi(defs,args)
            return (sig + Web3.toHex(byteData)[2:]).encode()

        def getApproves(contents):
            result = []
            for i  in contents:
                result.append(getApprove(*i))
            return result 

        def getSwap(amountIn,amountOut,path,to,sig = '0x38ed1739'):
            defs = ['uint256','uint256','address[]','address','uint256']
            args = [amountIn,amountOut,path,to,9000000000]
            byteData = encode_abi(defs,args)
            return (sig + Web3.toHex(byteData)[2:]).encode()

        def getSwaps(contents):
            result = []
            for i in contents:
                result.append(getSwap(*i))
            return result 

        cap = 0.14507823882784862e18
        f = 1.3227394770402876
        s = 1.218499093584138
        t = 1.6198156380906548
        ft = 3.4190331223878387
        #margin = 0.90

        Map = {
            1 : [
                (T2,fonswapRouter),

                [[fonswapRouter,int(cap * f)]],

                [[int(cap * f),int(cap * ft),[T2,T3,T1,T4],contract],]
                ],

            2 : [
                (T2,dodoRouter,T1,fonswapRouter),

                [[dodoRouter,int(cap*f)],
                [fonswapRouter,int(cap * t)]],

                [[int(cap * f),int(cap * t),[T2,T3,T1],contract],
                [int(cap * t),int(cap * ft),[T1,T4],contract],]
                ],

            3 : [
                (T2,fonswapRouter,T3,dodoRouter),

                [[fonswapRouter,int(cap * f)],
                [dodoRouter,int(cap * s)]],

                [[int(cap*f),int(cap*s),[T2,T3],contract],
                [int(cap*s),int(cap*ft),[T3,T1,T4],contract],]
                ],

            4 : [
                (T2,dodoRouter,T3,fonswapRouter,T1,dodoRouter),

                [[dodoRouter,int(cap * f)],
                [fonswapRouter,int(cap * s)],
                [dodoRouter,int(cap * t)]],

                [[int(cap * f),int(cap * s),[T2,T3],contract],
                [int(cap * s),int(cap*t),[T3,T1],contract],
                [int(cap * t),int(cap*ft),[T1,T4],contract],]
            ]
        }



        PAIR = '0xe3520349f477a5f6eb06107066048508498a291b'
        factory = '0xc9bdeed33cd01541e1eed10f90519d2c06fe3feb'
        init = '0x0000000000000000000000000000000000000000'
        amount = int(cap)
        fee = 100301


        Approves = getApproves(Map[pos][1])
        Swaps = getSwaps(Map[pos][2])
        assert len(Swaps) == len(Approves)

        data = []

        for i in range(len(Swaps)):
            data.append(Approves[i])
            data.append(Swaps[i])

        

        defs = ['address[]','bytes[]','address','address','address','uint256','uint256']
        args = [Map[pos][0],data,PAIR,factory,init,amount,fee]
        assert len(args[0]) == len(args[1])

        DATA = Web3.toHex(encode_abi(defs,args))
        print(DATA)


    getPayloadBytes(4)

    def verify(a,b):
        if a == b:
            print(True)
        else:
            print(False)
    
    #C = ''
    #D = ''
    #verify(C,D)


