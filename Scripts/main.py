from dotenv import load_dotenv
import Blockchains as Blc
import Config as Cfg
#import Controller as Ctr


if __name__ == '__main__':
    load_dotenv()

    chain = Blc.BSC()

    route = [{'from': 'TST4', 'to': 'TST2', 'via': 'fonswap'}, {'from': 'TST2', 'to': 'TST3', 'via': 'fonswap'}, {'from': 'TST3', 'to': 'TST1', 'via': 'fonswap'},{'from': 'TST1', 'to': 'TST4', 'via': 'fonswap'}]
    prices = [
        {'TST4' : 60, 'TST2' : 80},
        {'TST2' : 70, 'TST3' : 65},
        {'TST3' : 50, 'TST1' : 67},
        {'TST1' : 47, 'TST4' : 67}
    ]
    #print(chain.pollRoute(route))
    
    #ep = chain.simulateSwap(route,0.02867159537482727,prices)
    #print(ep)

    routes = chain.getArbRoute(graph = True, tokens = 'all', exchanges = 'all',save = False)
    chain.pollRoutes(routes)
    
    #controller = Ctr.Controller(chain)
    #print(controller.prepPayload(item = Cfg.ITEMS[0],options = Cfg.OPTIONS[0])[-1])

