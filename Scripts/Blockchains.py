if __name__ == '__main__':
    import Config as Cfg
    import Controller as Ctr
else:
    import scripts.Config as Cfg
    import scripts.Controller as Ctr

import requests, json, time, os

from functools import wraps


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

class Aurora():
    def __init__(self):
        self.source = 'https://explorer.mainnet.aurora.dev/api'
        self.impact = 0.005
        self.r1 = 0.997
        self.exchanges = Cfg.AuroraExchanges
        self.tokens = Cfg.AuroraTokens
        
        path = os.path.join(os.path.split(os.path.dirname(__file__))[0], 'data', 'Aurora', 'arbRoute.json')
        self.routePath = path
        self.params = Cfg.AuroraParams
        self.headers = Cfg.AuroraHeaders
        # the depth limited search depth
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

    @RateLimited(1)
    def getPrice(self, session, address):
        price = {}
        parameters = self.params
        parameters['address'] = address
        response = session.get(self.source, headers = self.headers, params = parameters)

        if response.status_code == 200:
            for i in response.json()['result']:
                price[i['symbol']] = int(i['balance']) / 10**int(i['decimals'])
        else:
            print('unsuccesful request!')

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
                except ConnectionError:
                    retries -= 1
                    time.sleep(30)
                    print(f'Connection error \nRetring {3 - retries}/3 ...')
                    
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

    def pollRoutes(self, routes = []):
        print('polling routes ...')
        if not routes:
            with open(self.routePath) as RO:
                routes = json.load(RO)

        cycle = 73

        result = []
        routeLenght = len(routes)
        for pos, route in enumerate(routes):
            if pos % cycle == 72:
                print('pausing for the api..')
                time.sleep(60)
            print(f'{pos + 1} / {routeLenght}')
            capital, rates, EP = self.pollRoute(route)
            result.append({
                'route' : route,
                'index' : rates[-1],
                'capital' : capital,
                'EP' : EP
            })

        return sorted(result, key = lambda v : v['EP'], reverse = True)
    
    def screenRoutes(self, expectedProfit = 50, routes = [], save = True):
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

        if save:
            with open(self.routePath,'w') as AR:
                json.dump(newRoute,AR,indent = 2)
        else:
            return newRoute    

    def executeArb(self, expectedProfit = 50, routes = []):
        if not routes:
            with open(self.routePath) as RO:
                routes = json.load(RO)

        for route in routes:
            _, _, EP = self.pollRoute(route)
            if EP >= expectedProfit:
                pass

route = [
    {
    'from' : 'AURORA',
    'to' : 'WETH',
    'via' : 'trisolaris'},
    {
    'from' : 'WETH',
    'to' : 'NEAR',
    'via' : 'wannaswap'},
    {
    'from' : 'NEAR',
    'to' : 'AURORA',
    'via' : 'wannaswap'},
    ]

if __name__ == '__main__':
    Aurora = Aurora()
    res = Aurora.pollRoute(route)
    print(res)
    '''
    results = Aurora.pollRoutes()
    path = os.path.join(os.path.split(os.path.dirname(__file__))[0], 'Dump.json')

    with open(path,'w') as DP:
        json.dump(results, DP, indent = 2)
    '''

          

 
