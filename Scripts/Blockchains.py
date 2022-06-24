from . import Config as Cfg
from . import Controller as Ctr
import requests, json, time, os

from functools import wraps
from bs4 import BeautifulSoup


def RateLimited(maxPerSecond):
    mininterval = 1.0 / float(maxPerSecond)

    def decorate(func):
        lastTimeCalled = [0.0]

        @wraps(func)
        def ratelimitedFunction(*args,**kwargs):
            elapsed = time.process_time_ns() - lastTimeCalled[0]
            lefttowait = mininterval - elapsed
            if lefttowait > 0:
                print(f'waiting {lefttowait} ...')
                time.sleep(lefttowait)
            ret = func(*args, **kwargs)
            lastTimeCalled[0] = time.process_time_ns()
            return ret
        return ratelimitedFunction
    return decorate


class Blockchain:
    def __init__(self):
        self.impact = 0.005
        self.r1 = 0.997
        self.depthLimit = 4
        self.graph = {}
        self.arbRoutes = []

    def buildGraph(self, exchanges = {}):
        graph = {}
        if not exchanges:
            exchanges = self.exchanges

        for dex, tokens in exchanges.items():
            for pools in tokens.keys():
                pool = list(pools)
                if pool[0] not in graph:
                    graph[pool[0]] = []
                if pool[1] not in graph:
                    graph[pool[1]] = []
                
                graph[pool[0]].append({'to' : pool[1], 'via' : dex})
                graph[pool[1]].append({'to' : pool[0], 'via' : dex})

        self.graph = graph    

    def dive(self, depth, node, goal, path, followed):
        result = []
        if depth <= self.depthLimit and node in self.graph:
            for i in self.graph[node]:
                if frozenset([i['to'],i['via'],path[-1]['to']]) in followed:
                    pass
                elif i['to'] == goal:
                    new_path = path + [i]
                    new_path[-1]['from'] = new_path[-2]['to']
                    result.append(new_path)
                elif depth < self.depthLimit:
                    followed.append(frozenset([i['to'],i['via'],path[-1]['to']]))
                    new_path = path + [i]
                    new_path[-1]['from'] = new_path[-2]['to']
                    result += self.dive(depth + 1, i['to'], goal,new_path, followed)
        
        return result

    def DLS(self,goal):
        # implementation of depth limited search
        result = []
        path = {'from': goal}
        followed = []
        depth = 1

        if goal in self.graph:
            start = self.graph[goal]
        else:
            start = []

        for i in start:
            followed.append(frozenset([goal,i['to'],i['via']]))
            new_path = [{**path, **i}]
            # recursive function to search the node to the specified depth
            result += self.dive(depth + 1, i['to'],goal,new_path,followed)
            followed = []

        return result
           
    def getArbRoute(self, tokens = 'default', graph = False, save = True):
        route = []

        if tokens == 'default':
            tokens = self.startTokens
        elif tokens == 'all':
            tokens = self.tokens.keys()

        if graph:
            self.buildGraph()

        for token in tokens:
            route += self.DLS(token)
    
        if save:
            with open(self.routePath,'w') as AR:
                json.dump(route,AR,indent = 2)
        else:
            return route

    def extract(self,content):
        price = {}
        soup = BeautifulSoup(content, 'html.parser')
        tokensList = soup.find_all('li',class_ = 'list-custom')
        #print(tokensList)
        for token in tokensList:
            try:
                raw = token.find(class_ = 'list-amount').string
                rawPrice = str(raw).split()
                price[rawPrice[1]] = float(rawPrice[0].replace(',',''))
            except:
                print('Error parsing html')
            
        return price
    
    @RateLimited(1)
    def getPrice(self, session, address):

        url = self.source + address
        response = session.get(url)
        
        if response.status_code == 200:
            price = self.extract(response.text)
        else:
            print('unsuccesful request!')
            print(response.status_code)

        return price

    def getRate(self, price, to, fro):
        return self.r1 * price[to] / (1 + (self.impact * self.r1)) / price[fro] 

    def pollRoute(self, route):
        rates = []
        liquidity = []
        least = 0
        lenght = len(route)
        session = requests.Session()

        for index, swap in enumerate(route):
            retries = 3
            done = False

            while retries and not done:
                try:
                    price = self.getPrice(
                        session, 
                        self.exchanges[swap['via']][frozenset([swap['from'],swap['to']])])
                except:
                    retries -= 1
                    time.sleep(10)
                    print(f'Error \nRetring {3 - retries}/3 ...')
                    
                else:
                    done = True

            print(price)
             
            rate = self.getRate(price, swap['to'], swap['from'])

            if index == 0:
                least = min(price[swap['from']],price[swap['to']])
                forward = price[swap['to']]
                rates.append(rate)

            elif index == lenght - 1:
                least = min(price[swap['from']],price[swap['to']],least)
                rates.append(rate * rates[-1])
                liquidity += [min(price[swap['from']],forward), price[swap['to']]]
            else:
                least = min(price[swap['from']],price[swap['to']],least)
                rates.append(rate * rates[-1])
                liquidity.append(min(price[swap['from']],forward))
                forward = price[swap['to']]

        try:
            index = liquidity.index(least)
        except ValueError:
            capital = least * self.impact
        else:
            capital = liquidity[index] / rates[index] * self.impact 

        EP = (capital * rates[-1]) - capital

        return [capital,rates,EP]

    def pollRoutes(self, routes = [], save = True):
        print('polling routes ...')
        if not routes:
            with open(self.routePath) as RO:
                routes = json.load(RO)

        result = []
        routeLenght = len(routes)
        try:
            for pos, route in enumerate(routes):
                print(f'{pos + 1} / {routeLenght}')
                capital, rates, EP = self.pollRoute(route)
                result.append({
                    'route' : route,
                    'index' : rates[-1],
                    'capital' : capital,
                    'EP' : EP
                })
        finally:
            export = sorted(result, key = lambda v : v['EP'], reverse = True)
        
            if save:
                with open(self.pollPath,'w') as DP:
                    json.dump(export, DP, indent = 2)
            
            else:
                return export
              
    def screenRoutes(self, expectedProfit = 50, routes = []):
        print('screening routes...')
        newRoute = []

        if not routes:
            with open(self.routePath) as RO:
                routes = json.load(RO)
        routeLenght = len(routes)

        for pos, route in enumerate(routes):
            print(f'{pos + 1} / {routeLenght}')
            _, _, EP = self.pollRoute(route)
            if EP >= expectedProfit:
                newRoute.append(route)
       
        with open(self.routePath,'w') as AR:
            json.dump(newRoute,AR,indent = 2)  

    def executeArb(self, expectedProfit = 50, routes = []):
        if not routes:
            with open(self.routePath) as RO:
                routes = json.load(RO)

        for route in routes:
            _, _, EP = self.pollRoute(route)
            if EP >= expectedProfit:
                pass

class Aurora(Blockchain):
    def __init__(self):
        super().__init__()
        self.source = 'https://aurorascan.dev/address/'
        self.exchanges = Cfg.AuroraExchanges
        self.tokens = Cfg.AuroraTokens
        self.startTokens = Cfg.AuroraStartTokens
        self.startExchanges = None

        self.pollPath = os.path.join(os.path.split(os.path.dirname(__file__))[0],
            'data', 'Aurora', 'pollResult.json')

        self.routePath = os.path.join(os.path.split(os.path.dirname(__file__))[0],
            'data', 'Aurora', 'arbRoutes.json')
        


class Arbitrum(Blockchain):
    def __init__(self):
        super().__init__()
        self.source = 'https://arbiscan.io/address/'
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None

        self.pollPath = os.path.join(os.path.split(os.path.dirname(__file__))[0],
            'data', 'Arbitrum', 'pollResult.json')

        self.routePath = os.path.join(os.path.split(os.path.dirname(__file__))[0],
            'data', 'Arbitrum', 'arbRoutes.json')

class BSC(Blockchain):
    def __init__(self):
        super().__init__()
        self.source = 'https://bscscan.com/address/'
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        
        self.pollPath = os.path.join(os.path.split(os.path.dirname(__file__))[0],
            'data', 'BSC', 'pollResult.json')

        self.routePath = os.path.join( os.path.split(os.path.dirname(__file__))[0],
            'data', 'BSC', 'arbRoute.json')
      


if __name__ == '__main__':
    chain = Aurora()
    chain.pollRoutes()
    

          

 
