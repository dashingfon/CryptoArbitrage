#from dotenv import load_dotenv
from brownie import interface
from copy import deepcopy

import scripts.Blockchains as Blc
import scripts.Config as Cfg
#import scripts.Controller as Ctr
from scripts.utills import sortTokens, readJson, writeJson


def Contract(idd,address):
    if idd == 'Factory':
        return interface.IFactory(address)
    elif idd == 'Router':
        return interface.IRouter(address)
    elif idd == 'Pair':
        return interface.IPair(address)
    else:
        raise ValueError

def test():
    factory = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'
    token0 = '0x55d398326f99059ff775485246999027b3197955'
    token1 = '0xe9e7cea3dedca5984780bafc599bd69add087d56'
    expectedPair = '0x7efaef62fddcca950418312c6c91aef321375a00'
    pair = interface.IFactory(factory).getPair(token0,token1)
    print(f'returned pair :- {pair}')
    print(f'expected pair :- {expectedPair}')

exchanges = Cfg.BSCExchanges
Chain = Blc.BSC()
config = readJson('Config.json')


def test_router_factories():
    routerLen = len(Chain.exchanges)
    page = 1
    for exchange, item in Chain.exchanges.items():
        print(f'\rPage {page} of {routerLen}')
        router = item['router']
        factory = item['factory']
        contract = Contract('Router',router)
        got = contract.factory().lower()
        if got != factory.lower():
            print(f'Exchange {exchange} router factory incorrect')
            print(f'Got :- {got}')
            print(f'Expected :- {factory.lower()}')
            print('')
        page += 1


def test_pairs_factories():
    excLen = len(Chain.exchanges)
    page = 1
    for exchange, item in Chain.exchanges.items():
        factory = Chain.exchanges[exchange]['factory']
        pair = 1
        for tokens, address in item['pairs'].items():
            print(f'\rExchange {page} of {excLen}, Pair {pair}')
            contract = Contract('Pair',address)
            got = contract.factory().lower()
            if got != factory.lower():
                print(f'Exchange {exchange}, Pair {tokens} factory incorrect')
                print(f'Got :- {got}')
                print(f'Expected :- {factory.lower()}')
                print('')
            pair += 1
        page += 1

def test_factories_pairs():
    toks = Chain.tokens
    excLen = len(Chain.exchanges)
    page = 1
    for exchange, item in Chain.exchanges.items():
        factory = Chain.exchanges[exchange]['factory']
        pair = 1
        for tokens, address in item['pairs'].items():
            print(f'\rExchange {page} of {excLen}, Pair {pair}')
            tokens = list(tokens)
            contract = Contract('Factory',factory)
            got = contract.getPair(toks[tokens[0]],toks[tokens[1]]).lower()
            if got != address.lower():
                print(f'Exchange {exchange}, Pair {tokens} incorrect')
                print(f'Got :- {got}')
                print(f'Expected :- {address.lower()}')
                print(f'Token addresses :- {(toks[tokens[0]],toks[tokens[1]])}')
                print('')
            pair += 1
        page += 1

def verify():
    Chain.getArbRoute(tokens = 'all')
    Chain.pollRoutes()

def main():
    #test_router_factories()
    #test_pairs_factories()
    test_factories_pairs()



#if __name__ == '__main__':
    #load_dotenv()

    #chain = Blc.BSC()

    #ep = chain.simulateSwap(route,0.02867159537482727,prices)
    #print(ep)

    #routes = chain.getArbRoute(tokens = 'all',save = False)
    #chain.pollRoutes(routes)
    
    #controller = Ctr.Controller(chain)
    #controller.arb(amount = 3)

    
