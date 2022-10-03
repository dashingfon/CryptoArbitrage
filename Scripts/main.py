# from dotenv import load_dotenv
# from brownie import interface
import asyncio
import aiohttp
from asyncio.proactor_events import _ProactorBasePipeTransport
import scripts.Blockchains as Blc
import scripts.Config as Cfg
# import scripts.Controller as Ctr
from scripts.utills import silence_event_loop_closed


exchanges = Cfg.BSCExchanges
Chain = Blc.BSC()
Route = [
      {
        "from": "WBNB_3bc095c",
        "to": "BSC-USD_3197955",
        "via": "pancakeswap_v2"
      },
      {
        "to": "BUSD_d087d56",
        "via": "pancakeswap_v2",
        "from": "BSC-USD_3197955"
      },
      {
        "to": "USDC_2cd580d",
        "via": "pancakeswap_v2",
        "from": "BUSD_d087d56"
      },
      {
        "to": "WBNB_3bc095c",
        "via": "pancakeswap_v2",
        "from": "USDC_2cd580d"
      }
    ]
# config = readJson('Config.json')


async def main():
    await Chain.pollRoutes()


if __name__ == '__main__':

    _ProactorBasePipeTransport.__del__ = silence_event_loop_closed(_ProactorBasePipeTransport.__del__)
    asyncio.run(main())

    # load_dotenv()

    # chain = Blc.BSC()

    # ep = chain.simulateSwap(route,0.02867159537482727,prices)
    # print(ep)

    # routes = chain.getArbRoute(tokens = 'all',save = False)
    # chain.pollRoutes(routes)

    # controller = Ctr.Controller(chain)
    # controller.arb(amount = 3)
