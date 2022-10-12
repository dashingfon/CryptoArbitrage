import asyncio
from asyncio.proactor_events import _ProactorBasePipeTransport
# from dotenv import load_dotenv
# from brownie import interface

import scripts.Blockchains as Blc
# import scripts.Config as Cfg
# import scripts.Controller as Ctr
from scripts.Utills import silence_event_loop_closed
# load_dotenv()
# config = readJson('Config.json')

_ProactorBasePipeTransport.__del__ = silence_event_loop_closed(  # type: ignore
        _ProactorBasePipeTransport.__del__)


async def main():

    # url = f'https://bsc.nownodes.io/{os.environ}'
    Chain = Blc.BSC()
    Chain.buildGraph()
    print(Chain.graph)
    '''routes = Chain.getArbRoute(tokens='default', save=False)
    await Chain.pollRoutes(routes=routes)'''


if __name__ == '__main__':
    asyncio.run(main())