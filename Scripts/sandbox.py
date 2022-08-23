#from functools import wraps
#import dotenv

#import time
from web3 import Web3
#import Controller as Ctr
#from ratelimit import limits, RateLimitException, sleep_and_retry

#from pycoingecko import CoinGeckoAPI
#import os
import json
from eth_abi import encode_abi

with open(r'scripts\Config.json') as CJ:
    config = json.load(CJ)

T1 = config['Test']['T1']
T2 = config['Test']['T2']
T3 = config['Test']['T3']
T4 = config['Test']['T4']
fonswapRouter = config['Test']['fonswapRouter']
dodoRouter = config['Test']['dodoRouter']
PAIR = config['Test']['PAIR']
cap = config['Test']['cap']
fee = config['Test']['fee']


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


    def Poll():
        #test = Blc.Aurora()
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
            {'TST1' : 47, 'TST4' : 67}
        ]


        #print(test.pollRoute(route = route, prices = prices))
   
    #print(test.assemble("TST4 TST2 fonswap - TST2 TST3 fonswap - TST3 TST1 fonswap - TST1 TST4 fonswap"))
    

    '''
    The getPayloadBytes function compiles the data as it would be calling prepPayload from the Controller class
    '''
    def getPayloadBytes(pos):
        assert 1 <= pos <= 4

        def getPaths(contents):
            num = 1
            result = []
            defs = ['address[]']
            for i in contents:
                args = [i]
                result.append(encode_abi(defs,args))
                print(f'address data {num} :- {Web3.toHex(encode_abi(defs,args))}')
            return result

        Map = {
            1 : [
                [fonswapRouter],
                [[T2,T3,T1,T4]]],

            2 : [
                [dodoRouter,fonswapRouter],
                [[T2,T3,T1],
                [T1,T4]]],

            3 : [
                [fonswapRouter,dodoRouter],
                [[T2,T3],
                [T3,T1,T4]]],

            4 : [
                [dodoRouter,fonswapRouter,dodoRouter],
                [[T2,T3],
                [T3,T1],
                [T1,T4]]]
        }

        data = getPaths(Map[pos][1])

        defs = ['address[]','bytes[]','address','uint256','uint256']
        args = [Map[pos][0],data,PAIR,int(cap),fee]
        assert len(args[0]) == len(args[1])

        DATA = Web3.toHex(encode_abi(defs,args))
        print(f'payload Data for {pos}')
        print(DATA)
        return DATA

    def setPreparedData():
        result = []
        for i in range(1,5):
            result.append(getPayloadBytes(i))
        config['Test']['PrepedSwapData'] = result
        with open(r'scripts\Config.json','w') as CJ:
            json.dump(config,CJ,indent = 2)

    '''for i in range(4):
        getPayloadBytes(i + 1)'''
    setPreparedData()
 

    def get():
        pass

    def fetchTokens():
        pass
    
    def setTokens():
        pass

    def fetchExchanges():
        pass
    
    def setExchanges():
        pass

    def fetchPairs():
        pass

    def buildExchangesData():
        pass

    
    
    