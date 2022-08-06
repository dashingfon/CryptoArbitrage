import Blockchains as Blc
import Config as Cfg
import Controller as Ctr


if __name__ == '__main__':

    chain = Blc.BSC()
    '''
    chain.getArbRoute(graph = True)
    chain.pollRoutes(start = 215)
    '''
    controller = Ctr.Controller(chain)
    print(controller.prepPayload(item = Cfg.ITEMS[0],options = Cfg.OPTIONS[0])[-1])