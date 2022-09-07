#from dotenv import load_dotenv
#from brownie import interface
from copy import deepcopy
import requests

import scripts.Blockchains as Blc
import scripts.Config as Cfg
#import scripts.Controller as Ctr
#from scripts.utills import sortTokens, readJson, writeJson


exchanges = Cfg.BSCExchanges
Chain = Blc.BSC()
#config = readJson('Config.json')


def main():
    Chain.pollRoutes()
    


main()


#if __name__ == '__main__':
    #load_dotenv()

    #chain = Blc.BSC()

    #ep = chain.simulateSwap(route,0.02867159537482727,prices)
    #print(ep)

    #routes = chain.getArbRoute(tokens = 'all',save = False)
    #chain.pollRoutes(routes)
    
    #controller = Ctr.Controller(chain)
    #controller.arb(amount = 3)

    
