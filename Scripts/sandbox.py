from collections import OrderedDict
import scripts.Blockchains as Blc
import scripts.utills as utills
# import scripts.Models as models
import time
# import abc
import asyncio
# import aiohttp
# import pathlib'''
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

    url = 'https://bsc-dataseed.binance.org'
    w3 = Web3(Web3.HTTPProvider(url))

    addresses = [
        Web3.toChecksumAddress("0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"),
        Web3.toChecksumAddress("0x55d398326f99059ff775485246999027b3197955"),
        Web3.toChecksumAddress("0xe9e7cea3dedca5984780bafc599bd69add087d56"),
        Web3.toChecksumAddress("0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82"),
        Web3.toChecksumAddress("0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"),
        Web3.toChecksumAddress("0x2170ed0880ac9a755fd29b2688956bd959f933f8"),
        Web3.toChecksumAddress("0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c"),
        Web3.toChecksumAddress("0xba2ae424d960c26247dd6c32edc70b295c744c43")
    ]
    abi = [
        {
        "inputs": [],
        "name": "factory",
        "outputs": [
            {
            "internalType": "address",
            "name": "",
            "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
        },
        {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {
            "internalType": "uint112",
            "name": "_reserve0",
            "type": "uint112"
            },
            {
            "internalType": "uint112",
            "name": "_reserve1",
            "type": "uint112"
            },
            {
            "internalType": "uint32",
            "name": "_blockTimestampLast",
            "type": "uint32"
            }
        ],
        "stateMutability": "view",
        "type": "function"
        },
    ]

    async def trid(address, abi=abi):
        Contract = w3.eth.contract(address=address, abi=abi)
        resu, gri, _ = Contract.functions.getReserves().call()
        return resu, gri

    async def reed():
        tasks = []
        for i in addresses:
            tasks.append(asyncio.create_task(trid(i)))

        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        results = []

        for p in pending:
            p.cancel()

        for item in done:
            results.append(await item)
            '''try:
                results.append(await item)
            except RuntimeError as e:
                print(e)'''

        print(len(done))
        print(results)


    asyncio.run(reed())
