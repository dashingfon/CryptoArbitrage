from collections import OrderedDict
import scripts.Blockchains as Blc
import scripts.utills as utills
import scripts.Models as models
import time
'''import abc
import asyncio
import aiohttp
import pathlib'''
# from bs4 import BeautifulSoup
from web3 import Web3
from web3.eth import AsyncEth
# import scripts.Config as Cfg
# import datetime, os
# from cache import AsyncTTL
from asyncio.proactor_events import _ProactorBasePipeTransport
# from brownie import interface


route = [
    {"from": "TST4", "to": "TST2", "via": "fonswap"},
    {"from": "TST2", "to": "TST3", "via": "fonswap"},
    {"from": "TST3", "to": "TST1", "via": "fonswap"},
    {"from": "TST1", "to": "TST4", "via": "fonswap"}
]
prices = [
    {'TST4': 60, 'TST2': 80},
    {'TST2': 70, 'TST3': 65},
    {'TST3': 50, 'TST1': 67},
    {'TST1': 47, 'TST4': 67}
]

config = utills.config


def pullDataFromDump(chain, exchanges, temp=False):
    path = r'data\dataDump.json'
    utills.setExchangesData(chain, path, exchanges, temp)


def findSymbol(symbol):
    tokens = utills.readJson(r'data\artifactDump.json')['tokens']
    print(tokens[symbol])


def pull():
    chain = Blc.BSC()
    tokens = utills.readJson(r'data\artifactDump.json')['tokens']
    exchanges = utills.readJson(r'data\artifactDump.json')['exchanges']
    trimmed = utills.trim_and_map(chain, tokens, exchanges)
    trimmed['MetaData']['datetime'] = time.ctime()
    utills.writeJson(r'data\dataDump.json', trimmed)


def main():
    chain = Blc.Aurora()
    utills.buildData(chain, minLiquidity=75000, saveArtifact=True)
    # pullDataFromDump(chain,Cfg.AuroraExchanges,True)


if __name__ == '__main__':
    # main()
    _ProactorBasePipeTransport.__del__ = utills.silence_event_loop_closed(
        _ProactorBasePipeTransport.__del__)

    chain = Blc.BSC()

    def evalExchanges(batch):
        routes = utills.readJson(chain.routePath)['Data']
        distribution = OrderedDict()
        exchanges = chain.exchanges
        batches = utills.split_list(routes, batch)
        print(f'lenght of routes :- {len(routes)}')
        lenght = 0

        for item in batches:
            store = set()
            for route in item:
                for swap in route:
                    store.add(exchanges[swap['via']]['pairs']
                              [frozenset([swap['from'], swap['to']])])
            if len(store) not in distribution:
                distribution[len(store)] = 0
            distribution[len(store)] += 1
            lenght += 1

        print(f'lenght of batches :- {lenght}')
        print(distribution)

    def evalExchanges2():
        routes = utills.readJson(chain.routePath)['Data']
        distribution = OrderedDict()
        exchanges = chain.exchanges
        batches = utills.split_list2(routes)
        print(f'lenght of routes :- {len(routes)}')
        lenght = 0
        store = set()

        for item in batches:
            count = 0
            for route in item:
                for swap in route:
                    load = exchanges[swap['via']]['pairs'][
                        frozenset([swap['from'], swap['to']])]
                    if load not in store:
                        count += 1
                    store.add(load)
            if count not in distribution:
                distribution[count] = 0
            distribution[count] += 1
            lenght += 1

        print(f'lenght of batches :- {lenght}')
        print(distribution)

    # evalExchanges2()
    # evalExchanges(15)

    class Rive:
        def __init__(self, val, amount=8) -> None:
            self.val = val
            self.amount = amount

        def __iter__(self) -> 'Rive':
            return self

        def __next__(self) -> None:
            if self.amount:
                print(self.val)
                self.amount -= 1
            else:
                raise StopIteration

    e = Rive(7)
    for i in e:
        pass

    
