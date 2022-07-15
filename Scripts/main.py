import Blockchains as Blc
import Controller as Ctr
#import brownie


if __name__ == '__main__':
    chain = Blc.BSC()
    chain.getArbRoute(graph = True)
    chain.pollRoutes()