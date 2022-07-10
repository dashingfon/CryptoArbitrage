'''
This module contains the Blockchain main class that other specific blockchain classes inherit from
to import the config and controller modules
'''
import Config as Cfg
import Controller as Ctr

'''
Then to import the other modules needed
'''
import requests, json, time, os, warnings
from functools import wraps
from bs4 import BeautifulSoup

'''
This is the Ratelimited function used to decorate the getPrice function that limits the rate
at which requests are being sent
'''
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

'''
the main blockchain class containing all the methods
'''
class Blockchain:
    def __init__(self):
        self.impact = 0.005 # represents the fraction of the liquidity pool 
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

    def DLS(self,goal,exchanges):
        # implementation of depth limited search
        start = []
        result = []
        path = {'from': goal}
        followed = []
        depth = 1

        if exchanges == 'default':
            exchanges = self.startExchanges

        if goal in self.graph and exchanges == 'all':
            start = self.graph[goal]
                 
        elif goal in self.graph:
            for i in self.graph[goal]:
                if i['via'] in exchanges:
                    start.append(i)  

        for i in start:
            followed.append(frozenset([goal,i['to'],i['via']]))
            new_path = [{**path, **i}]
            # recursive function to search the node to the specified depth
            result += self.dive(depth + 1, i['to'],goal,new_path,followed)
            followed = []

        return result
           
    def getArbRoute(self, tokens = 'default', exchanges = 'all',graph = False, save = True):
        route = []

        if graph:
            self.buildGraph()

        # add functionality to get routes from specific start exchanges

        if tokens == 'default':
            tokens = self.startTokens
        elif tokens == 'all':
            tokens = self.tokens.keys()

        if exchanges == 'default':
            exchanges = self.startExchanges
        
        if type(tokens) != list:
            raise ValueError('invalid token argument')
        
        if type(exchanges) != list and exchanges != 'all':
            raise ValueError('invalid token argument')

        for token in tokens:
            route += self.DLS(token,exchanges)
    
        if save:
            with open(self.routePath,'w') as AR:
                json.dump(route,AR,indent = 2)
        else:
            return route

    def extract(self,content,swap):
        price = {}
        soup = BeautifulSoup(content, 'html.parser')

        try:
            tokensList = soup.find_all('li',class_ = 'list-custom')
            #print(tokensList)
            done1 = False
            done2 = False
            slider = 0
            while (not done1 or not done2) and slider < len(tokensList):  
                raw = tokensList[slider].find(class_ = 'list-amount').string
                rawPrice = str(raw).split()
                price[rawPrice[1]] = float(rawPrice[0].replace(',',''))
                if rawPrice[1] == swap['from']:
                    done1 = True
                elif rawPrice[1] == swap['to']:
                    done2 = True
                slider += 1  

        except:
            print('Error parsing html')
            
        return price
    
    @RateLimited(1)
    def getPrice(self, session, address,swap):
        url = self.source + address
        attemptsAllowed = 4
        tries = 0
        done = False

        while tries < attemptsAllowed and not done:
                try:
                    response = session.get(url,headers = self.headers)
                except ConnectionError:
                    print('Error')
                    time.sleep(8)
                    tries += 1
                    print(f'Retring... \n{attemptsAllowed - tries} tries left')
                else:
                    done = True
        
        
        if response.status_code == 200:
            price = self.extract(response.text,swap)
        else:
            price = {}
            print('unsuccesful request!')
            print(response.status_code)

        return price

    def getRate(self, price, to, fro):
        if (to not in price) or (fro not in price):
            raise ValueError('currency not in price dictionary')

        return self.r1 * price[to] / (1 + (self.impact * self.r1)) / price[fro] 

    def getDetails(self,listItems,least,rates):
        try:
            index = listItems.index(least)
        except ValueError:
            capital = least * self.impact
        else:
            capital = listItems[index] / rates[index] * self.impact 
        
        EP = (capital * rates[-1]) - capital
        return [capital,rates,EP]

    def cumSum(self,listItem):
        result = [listItem[0]]
        for i in listItem[1:]:
            result.append(i*result[-1])
        return result

    def simplyfy(self,route):
        result = [route[0]['from']+' '+route[0]['to']+' '+route[0]['via']]
        _result = [route[0]['to']+' '+route[0]['from']+' '+route[0]['via']]

        for j in route[1:]:
            result.append(j['from']+' '+j['to']+' '+j['via'])
            _result.insert(0,j['to']+' '+j['from']+' '+j['via'])
            
        return ['-'.join(result),'-'.join(_result)]

    def pollRoute(self, route):
        rates = [[],[]]
        liquidity = [[],[]]
        least = 0
        lenght = len(route)
        session = requests.Session()

        for index, swap in enumerate(route):
            
            price = self.getPrice(
                session, 
                self.exchanges[swap['via']][frozenset([swap['from'],swap['to']])],
                swap)

            print(price)
             
            rate = (self.getRate(price, swap['to'], swap['from']),
            self.getRate(price, swap['from'], swap['to']))

            if index == 0:
                least = min(price[swap['from']],price[swap['to']])
                liquidity[0].append(price[swap['from']])
                forward = price[swap['to']]
                rates[0].append(rate[0])
                rates[1].insert(0,rate[1])
                
            else:
                least = min(price[swap['from']],price[swap['to']],least)
                rates[0].append(rate[0] * rates[0][-1])
                rates[1].insert(0,rate[1])
                liquidity[0].append(min(price[swap['from']],forward))

                if index == lenght - 1:
                    liquidity[0].append(price[swap['to']])
                forward = price[swap['to']]

        liquidity[1] = liquidity[0][-2::-1]
        liquidity[0] = liquidity[0][1:]
        rates[1] = self.cumSum(rates[1])

        export = (self.getDetails(liquidity[0],least,rates[0]),
            self.getDetails(liquidity[1],least,rates[1]))

        return export

    def pollRoutes(self, routes = [], save = True):
        print('polling routes ...')
        if not routes:
            with open(self.routePath) as RO:
                routes = json.load(RO)

        history = {}
        result = []
        routeLenght = len(routes)
    
        try:
            for pos, route in enumerate(routes):
                simplifiedroute = self.simplyfy(route)
                if simplifiedroute[0] in history or simplifiedroute[1] in history:
                    warnings.warn('route {simplifiedroute} already polled!')
                    continue

                print(f'{pos + 1} / {routeLenght}')
                # self.polRoute returns a tuple of [capital,rates,Ep]
                for P, item in enumerate(self.pollRoute(route)):
                    capital, rates, EP = item
                    result.append({
                        'route' : simplifiedroute[P],
                        'index' : rates[-1],
                        'capital' : capital,
                        'EP' : EP
                    })

                history[simplifiedroute[0]] = pos
                history[simplifiedroute[1]] = pos

            print('Done!')
        finally:
            export = sorted(result, key = lambda v : v['index'], reverse = True)
        
            if save:
                with open(self.pollPath,'w') as DP:
                    json.dump(export, DP, indent = 2)
            else:
                return (export,history)
              
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

    def executeArb(self, expectedProfit = 50, routes = [],save = True):
        if not routes:
            with open(self.routePath) as RO:
                routes = json.load(RO)

        for route in routes:
            _, _, EP = self.pollRoute(route)

'''
To do list
convert getarbroute to a generator to conserve memory or read it and iterate using a generator
integrate screenroutes with pollroutes using a cutoff parameter
'''
class Aurora(Blockchain):
    def __init__(self):
        super().__init__()
        self.source = 'https://aurorascan.dev/address/'
        self.exchanges = Cfg.AuroraExchanges
        self.tokens = Cfg.AuroraTokens
        self.startTokens = Cfg.AuroraStartTokens
        self.startExchanges = None
        self.headers = {}

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
        self.headers = {}

        self.pollPath = os.path.join(os.path.split(os.path.dirname(__file__))[0],
            'data', 'Arbitrum', 'pollResult.json')

        self.routePath = os.path.join(os.path.split(os.path.dirname(__file__))[0],
            'data', 'Arbitrum', 'arbRoutes.json')

class BSC(Blockchain):
    def __init__(self):
        super().__init__()
        self.source = 'https://bscscan.com/address/'
        self.exchanges = Cfg.BSCExchanges
        self.tokens = Cfg.BSCTokens
        self.startTokens = Cfg.BSCStartTokens
        self.startExchanges = Cfg.BSCStartExchanges
        self.headers = {
        'User-Agent': 'PostmanRuntime/7.29.0',}

        self.pollPath = os.path.join(os.path.split(os.path.dirname(__file__))[0],
            'data', 'BSC', 'pollResult.json')

        self.routePath = os.path.join( os.path.split(os.path.dirname(__file__))[0],
            'data', 'BSC', 'arbRoute.json')
      



    

          

 
