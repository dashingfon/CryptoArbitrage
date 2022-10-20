import asyncio
from asyncio.proactor_events import _ProactorBasePipeTransport
import pprint
import os
from dotenv import load_dotenv
from web3 import Web3

import scripts.Blockchains as Blc
from scripts.Utills import silence_event_loop_closed, writeJson, readJson

_ProactorBasePipeTransport.__del__ = silence_event_loop_closed(  # type: ignore
        _ProactorBasePipeTransport.__del__)
load_dotenv()


async def pollRoute():

    url = 'https://bsc-dataseed.binance.org'
    # url2 = f'https://bsc.nownodes.io/{os.environ.get("NowNodesBscKey")}'
    # url3 = f'https://solitary-few-flower.bsc.quiknode.pro/{os.environ.get("Quicknode")}'
    Chain = Blc.BSC(url=url)
    routes = Chain.getArbRoute(save=False)
    await Chain.pollRoutes(routes=routes)


def setup():
    Chain = Blc.BSC()
    Chain.setup(saveArtifact=True)


def checkAddressesNotInLookup():
    path = 'data\\PriceLookup.json'
    Chain = Blc.BSC()
    Chain.buildGraph()
    Chain.lookupPrice()
    pricelookup = readJson(path)

    result = []
    count = 0
    for i in Chain.graph.keys():
        count += 1
        if i.address not in pricelookup:
            result.append(i)

    print('the following are not included')
    pprint.pprint(result)
    print(f'total of {count} tokens')


def editConfig():
    Chain = Blc.BSC()
    tokens = {}
    exchanges = {}

    for key, item in Blc.Config[str(Chain)]['Tokens'].items():
        tokens[key] = Web3.toChecksumAddress(item)

    for key, value in Blc.Config[str(Chain)]['Exchanges'].items():
        temp = {}
        exchanges[key] = value
        for toks, addresses in value['pairs'].items():
            temp[toks] = Web3.toChecksumAddress(addresses)
        exchanges[key]['pairs'] = temp

    config = Blc.Config
    config[str(Chain)]['Tokens'] = tokens
    config[str(Chain)]['Exchanges'] = exchanges
    writeJson(Blc.CONFIG_PATH, config)


async def main():
    # url = f'https://bsc.nownodes.io/{os.environ}'
    Chain = Blc.BSC()
    Chain.getArbRoute()
    # pprint.pprint(Chain.exchanges)

if __name__ == '__main__':
    asyncio.run(pollRoute())
