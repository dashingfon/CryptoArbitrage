import asyncio
from asyncio.proactor_events import _ProactorBasePipeTransport
# import pprint
import os
from dotenv import load_dotenv

import scripts.Blockchains as Blc
from scripts.Utills import silence_event_loop_closed

_ProactorBasePipeTransport.__del__ = silence_event_loop_closed(  # type: ignore
        _ProactorBasePipeTransport.__del__)
load_dotenv()


async def pollRoute():

    # url = 'https://bsc-dataseed.binance.org'
    url2 = f'https://bsc.nownodes.io/{os.environ.get("NowNodesBscKey")}'
    Chain = Blc.BSC(url=url2)
    '''routes = Chain.getArbRoute(tokens='default', save=False)
    await Chain.pollRoutes(routes=routes)'''


async def main():
    # url = f'https://bsc.nownodes.io/{os.environ}'
    Chain = Blc.BSC()
    Chain.getArbRoute()
    # pprint.pprint(Chain.exchanges)

if __name__ == '__main__':
    asyncio.run(main())
