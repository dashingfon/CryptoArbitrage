import asyncio
from asyncio.proactor_events import _ProactorBasePipeTransport
import pprint
import os
from dotenv import load_dotenv
import logging

import scripts.Blockchains as Blc
import scripts.Controller as Ctr
from scripts.Models import Route
from scripts.Utills import silence_event_loop_closed, readJson, profiler


_ProactorBasePipeTransport.__del__ = silence_event_loop_closed(  # type: ignore
        _ProactorBasePipeTransport.__del__)

load_dotenv()


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


def forge():
    url3 = f'https://solitary-few-flower.bsc.quiknode.pro/{os.environ.get("Quicknode")}'
    Chain = Blc.BSC(url3)
    Cont = Ctr.Controller(blockchain=Chain, testing=False)
    routes = Chain.getArbRoute(save=False)
    cache = asyncio.run(Chain.buildCache(routes=routes, save=True))
    arbs = Cont.findAll(cache=cache, routes=routes)
    print(arbs)


def findALlTest():
    route = {
        "swaps": [
            {
            "fro": {
                "name": "WBNB",
                "address": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
            },
            "to": {
                "name": "BSC-USD",
                "address": "0x55d398326f99059fF775485246999027B3197955"
            },
            "via": {
                "name": "pancakeswap_v2",
                "pair": "0x16b9a82891338f9bA80E2D6970FddA79D1eb0daE",
                "fee": 99750,
                "router": "0x10ED43C718714eb63d5aA57B78B54704E256024E"
            }
            },
            {
            "fro": {
                "name": "BSC-USD",
                "address": "0x55d398326f99059fF775485246999027B3197955"
            },
            "to": {
                "name": "WBNB",
                "address": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
            },
            "via": {
                "name": "pancakeswap_v2",
                "pair": "0x16b9a82891338f9bA80E2D6970FddA79D1ebbbbE",
                "fee": 99750,
                "router": "0x10ED43C718714eb63d5aA57B78B54704E256024E"
            }
            }
        ],
        "simplyfied_short": "WBNB_3bc095c BSC-USD_3197955 pancakeswap_v2 - BSC-USD_3197955 WBNB_3bc095c pancakeswap_v2",
        "UsdValue": 283.54,
        "EP": 0,
        "rates": [],
        "capital": 0
    }
    cache = {
        "0x16b9a82891338f9bA80E2D6970FddA79D1eb0daE":
        {
            Blc.Token(
                name="WBNB",
                address="0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
            ): 500,
            Blc.Token(
                name="BSC-USD",
                address="0x55d398326f99059fF775485246999027B3197955"
            ): 600
        },
        "0x16b9a82891338f9bA80E2D6970FddA79D1ebbbbE":
        {
            Blc.Token(
                name="WBNB",
                address="0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
            ): 700,
            Blc.Token(
                name="BSC-USD",
                address="0x55d398326f99059fF775485246999027B3197955"
            ): 400
        }
    }
    Chain = Blc.BSC()
    Cont = Ctr.Controller(blockchain=Chain, testing=True)
    arbs = Cont.findAll(cache=cache, routes=[Blc.Route.fromDict(route)])
    print(arbs)


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
    forge()
    # findALlTest()
