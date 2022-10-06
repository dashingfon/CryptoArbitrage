import pathlib
import logging
import logging.config
import asyncio
from asyncio.proactor_events import _ProactorBasePipeTransport
# from dotenv import load_dotenv
# from brownie import interface


import scripts.Blockchains as Blc
# import scripts.Config as Cfg
# import scripts.Controller as Ctr
from scripts.utills import silence_event_loop_closed

path = pathlib.PurePath(__file__).parent.parent
logging.config.fileConfig(str(path.joinpath("logging.conf")))
Chain = Blc.BSC()

# config = readJson('Config.json')


async def main():

    _ProactorBasePipeTransport.__del__ = silence_event_loop_closed(
        _ProactorBasePipeTransport.__del__)

    routes = Chain.getArbRoute(tokens='default', save=False)
    print(len(routes))
    await Chain.pollRoutes(batch=10, routes=routes)


if __name__ == '__main__':

    asyncio.run(main())

    # load_dotenv()

    # chain = Blc.BSC()

    # ep = chain.simulateSwap(route,0.02867159537482727,prices)
    # print(ep)

    # routes = chain.getArbRoute(tokens = 'all',save = False)
    # chain.pollRoutes(routes)

    # controller = Ctr.Controller(chain)
    # controller.arb(amount = 3)
