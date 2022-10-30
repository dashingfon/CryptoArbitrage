import asyncio
from asyncio.proactor_events import _ProactorBasePipeTransport
import pprint
import os
from dotenv import load_dotenv
import logging

import scripts.Blockchains as Blc
from scripts.Utills import silence_event_loop_closed, readJson


_ProactorBasePipeTransport.__del__ = silence_event_loop_closed(  # type: ignore
        _ProactorBasePipeTransport.__del__)

load_dotenv()


async def pollRoute():
    # url = 'https://bsc-dataseed.binance.org'
    url3 = f'https://solitary-few-flower.bsc.quiknode.pro/{os.environ.get("Quicknode")}'
    # url2 = f'https://bsc.nownodes.io/{os.environ.get("NowNodesBscKey")}'
    Chain = Blc.BSC(url=url3)
    '''
    await Chain.pollRoutes(routes=routes)'''


def formCache():
    cache = readJson('data\\SampleCache.json')
    result = {}
    for k, v in cache.items():
        temp = {}
        for i, j in v.items():
            name = i.split('_')
            temp[Blc.Token(name[0], name[1])] = j
        result[k] = temp

    return result


def findAll(cache: dict, routes: list[Blc.Route]):
    for route in routes:
        pass


def forge():
    pass


async def main():
    # url = f'https://bsc.nownodes.io/{os.environ}'
    url3 = f'https://solitary-few-flower.bsc.quiknode.pro/{os.environ.get("Quicknode")}'
    Chain = Blc.BSC(url=url3)
    # Chain.buildGraph()
    routes = Chain.getArbRoute(save=False)
    await Chain.buildCache(routes=routes, save=True)
    # pprint.pprint(Chain.exchanges)


if __name__ == '__main__':
    # asyncio.run(main())
    print(formCache())
