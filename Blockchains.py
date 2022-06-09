import Config as Cfg
import Controller as Ctr
import requests, json

from functools import wraps

class limiter():
    def __init__(self, amount, period):
        pass

    def __call__(self, func):
        @wraps(func)
        def wrapper():
            originalResult = func()
            # needs editing
            modifiedResult = 6
            return modifiedResult
        return wrapper


class Aurora():
    
    def __init__(self):
        self.source = 'https://explorer.mainnet.aurora.dev/api'
        self.impact = 0.005
        self.r1 = 0.997
        self.exchanges = Cfg.AuroraExchanges
        self.tokens = Cfg.AuroraTokens
        self.routePath = r'Data\Aurora\arbRoute.json'
        self.params = Cfg.AuroraParams
        self.headers = Cfg.AuroraHeaders
        # the depth limited search depth
        self.depthLimit = 4
        self.graph = {}
        self.arbRoutes = []

    
    def getPrice(self, session, address):
        price = {}
        parameters = self.params
        parameters['address'] = address
        response = session.get(self.source, headers = self.headers, params = parameters)

        if response.status_code == 200:
            for i in response.json()['result']:
                price[i['symbol']] = int(i['balance']) / 10**int(i['decimals'])
        
        return price
        

    def buildGraph(self):
        graph = {}
        for dex, tokens in self.exchanges.items():
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
        
        return result
           
    def getArbRoute(self, tokens = Cfg.startTokens,save = True):
        route = []

        if not tokens:
            tokens = self.tokens.keys()
    
        for token in tokens:
            route += self.DLS(token)
    
        if save:
            with open(self.routePath,'w') as AR:
                json.dump(route,AR,indent = 2)
        else:
            return route

    def pollRoute(self, route):
        rates = []
        liquidity = []
        least = 0
        lenght = len(route)
        session = requests.Session()

        for index, swap in enumerate(route):

            price = self.getPrice(
                session, 
                Cfg.AuroraExchanges[swap['via']][frozenset([swap['from'],swap['to']])])

            rate = self.r1 * price[swap['to']] / (1 + (self.impact * self.r1)) / price[swap['from']] 
                
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
            capital = liquidity[index] * rates[index] * self.impact 

        EP = (capital * rates[-1]) - capital

        return [capital,rates[-1],EP]

    def pollRoutes(self, routes = []):
        if not routes:
            with open(self.routePath) as RO:
                routes = json.load(RO)

        result = []

        for route in routes:
            capital, index, EP = self.pollRoute(route)
            result.append({
                'route' : route,
                'index' : index,
                'capital' : capital,
                'EP' : EP
            })

        return sorted(result, key = lambda v : v['EP'])
    
    def screenRoutes(self, expectedProfit = 50, routes = [], save = True):
        newRoute = []
        if not routes:
            with open(self.routePath) as RO:
                routes = json.load(RO)

        for route in routes:
            _, _, EP = self.pollRoute(route)
            if EP >= expectedProfit:
                newRoute.append(route)

        if save:
            with open(self.routePath,'w') as AR:
                json.dump(newRoute,AR,indent = 2)
        else:
            return newRoute    

    def executeArb(self, capital = 100, index = 1.1, routes = []):
        if not routes:
            with open(self.routePath) as RO:
                routes = json.load(RO)

        for route in routes:
            Capital, Index = self.pollRoute(route)
            if Capital >= capital and Index >= index:
                pass


Aurora = Aurora()

'''
Aurora.buildGraph()
#print(Aurora.graph)
Aurora.getArbRoute()
'''
price = Aurora.getPrice(requests.Session(), '0xec538fafafcbb625c394c35b11252cef732368cd')
print(price)
# test get price
# then poll route
          


