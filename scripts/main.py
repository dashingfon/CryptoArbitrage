import asyncio
from asyncio.proactor_events import _ProactorBasePipeTransport
import pprint
import os
from dotenv import load_dotenv
import logging

import scripts.Blockchains as Blc
from scripts.Utills import silence_event_loop_closed

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


async def main():
    # url = f'https://bsc.nownodes.io/{os.environ}'
    url3 = f'https://solitary-few-flower.bsc.quiknode.pro/{os.environ.get("Quicknode")}'
    Chain = Blc.BSC(url=url3)
    # Chain.buildGraph()
    routes = Chain.getArbRoute(save=False)
    cache = await Chain.buildCache(routes)
    logging.info(cache)
    # pprint.pprint(Chain.exchanges)


def troubleShoot():
    EXCHANGES = {
        "trisolaris": {
            "pairs": {
                "AURORA_3bc095c - WETH_3bc095c":
                    "0x5eeC60F348cB1D661E4A5122CF4638c7DB7A886e",
                "NEAR_3bc095c - USDT_3bc095c":
                    "0x03B666f3488a7992b2385B12dF7f35156d7b29cD"
                },
            'fee': 94550,
            'router': '0x03B666f3488a7992b2385B12dF7f35156d7b29cD'

        },
        "auroraswap": {
            "pairs": {
                "USDT_3bc095c - USDC_3bc095c":
                    "0xec538fafafcbb625c394c35b11252cef732368cd",
                "USDC_3bc095c - NEAR_3bc095c":
                    "0x480a68ba97d70495e80e11e05d59f6c659749f27"
                },
            'fee': 94550,
            'router': '0x03B666f3488a7992b2385B12dF7f35156d7b29cD'
        },
        "wannaswap": {
            "pairs": {
                "AURORA_3bc095c - NEAR_3bc095c":
                    "0x7e9ea10e5984a09d19d05f31ca3cb65bb7df359d",
                "NEAR_3bc095c - WETH_3bc095c":
                    "0x256d03607eee0156b8a2ab84da1d5b283219fe97",
                "USDC_3bc095c - NEAR_3bc095c":
                    "0xbf560771b6002a58477efbcdd6774a5a1947587b"
                },
            'fee': 94550,
            'router': '0x03B666f3488a7992b2385B12dF7f35156d7b29cD'
        }
        }

    TOKENS = {
        'AURORA_3bc095c': "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
        'WETH_3bc095c': "0xcb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
        'USDC_3bc095c': "0xeb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
        'NEAR_3bc095c': "0xfb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
        'USDT_3bc095c': "0x1b4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
    }
    Chain = Blc.Test()
    routes = Chain.getArbRoute(tokens=TOKENS, exchanges=EXCHANGES,
                               save=False, livePrice=0.55)
    pprint.pprint(routes)


if __name__ == '__main__':
    asyncio.run(main())
    # troubleShoot()
