import os
from dotenv import load_dotenv
import Blockchains as Blc
#import Controller as Ctr


if __name__ == '__main__':
    load_dotenv()

    chain = Blc.BSC()

    #ep = chain.simulateSwap(route,0.02867159537482727,prices)
    #print(ep)

    routes = chain.getArbRoute(tokens = 'all',save = False)
    chain.pollRoutes(routes)
    
    #controller = Ctr.Controller(chain)
    #controller.arb(amount = 3)

