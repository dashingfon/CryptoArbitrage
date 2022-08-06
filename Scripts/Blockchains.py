'''
Blockchain module containing the different blockchain implementation
'''
#The config file contains related blockchain specific information

import Config as Cfg

'''
Then to import the other modules needed
'''
import requests, json, time, os, warnings
from functools import wraps
from bs4 import BeautifulSoup
from pycoingecko import CoinGeckoAPI

'''
This is the Ratelimited decorator used to limit requests
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
The main blockchain class other specific blockchains inherit
It contains all the methods
'''
class Blockchain:
    def __init__(self):
        self.impact = 0.005  
        self.r1 = 0.997 
        self.depthLimit = 4
        self.graph = {}
        self.arbRoutes = []
        self.dataPath = os.path.join(os.path.split(os.path.dirname(__file__))[0],
            'data')
        self.priceLookupPath = os.path.join(self.dataPath,'PriceLookup.json')

    '''
    impact - the amount of price impact allowed
    r1 - The swap fee on dexs
    depthLimit - Used to determine the longest cycle of swaps
    graph - a representation of the connected tokens across dexs
    arbRoutes - a list of the cycle able routes
    dataPath - the path to the data directory
    
    '''

    def buildGraph(self, exchanges = {}):
        # The method to find the connections between the tokens

        graph = {}
        if not exchanges:
            exchanges = self.exchanges

        for dex, attributes in exchanges.items():
            for pools in attributes['pairs'].keys():
                pool = list(pools)
                if pool[0] not in graph:
                    graph[pool[0]] = []
                if pool[1] not in graph:
                    graph[pool[1]] = []
                
                graph[pool[0]].append({'to' : pool[1], 'via' : dex})
                graph[pool[1]].append({'to' : pool[0], 'via' : dex})

        self.graph = graph    

    def dive(self, depth, node, goal, path, followed):
        # Used recurrsively with the Depth limited search function to discover tradable arb routes

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
           
    def getArbRoute(self, tokens = 'default', exchanges = 'all',graph = True, save = True):
        # The methods the produces and optionally saves the Arb routes

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
                json.dump(
                    {'MetaData': {
                        'time': time.ctime(),
                        'startExchanges' : self.startExchanges,
                        'startTokens' : self.startTokens,
                    },
                    'Data':route},
                    AR,indent = 2)
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
    
    @RateLimited(3)
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
                    time.sleep(10)
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
        reverseRoute = [{
            'from' : route[0]['to'],
            'to' :  route[0]['from'],
            'via' : route[0]['via']
        }]

        for j in route[1:]:
            result.append(j['from']+' '+j['to']+' '+j['via'])
            _result.insert(0,j['to']+' '+j['from']+' '+j['via'])
            reverseRoute.insert(0,{
            'from' : j['to'],
            'to' :  j['from'],
            'via' : j['via']
        })
            
        return [' - '.join(result),' - '.join(_result),route,reverseRoute]

    def assemble(self,route):
        result = []
        routeList = route.split(' - ')
        for item in routeList:
            itemList = item.split()
            load = {
                'from' : itemList[0],
                'to' : itemList[1],
                'via' : itemList[2],
            }
            result.append(load)
        return result

    def pollRoute(self, route, prices = []):
        rates = [[],[]]
        liquidity = [[],[]]
        least = 0
        lenght = len(route)
        session = requests.Session()

        if prices:
            assert len(prices) == lenght

        for index, swap in enumerate(route):
            if not prices:
                price = self.getPrice(
                    session, 
                    self.exchanges[swap['via']]['pairs'][frozenset([swap['from'],swap['to']])],
                    swap)

                print(price)
            else:
                price = prices[index]
             
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
    
    def checkIfTestnet(self):
            return str(self)[-7:] == 'Testnet'

    def lookupPrice(self, returns = False):
        def getPriceLookup():
            try:
                with open(self.priceLookupPath) as PP:
                    temp = json.load(PP)
            except FileNotFoundError:
                temp = {}
            
            return temp
        
        temp = getPriceLookup()

        Testnet = self.checkIfTestnet()
        prices = {}
        if not Testnet:

            tokenAdresses = []
            for i in self.tokens.values():
                tokenAdresses.append(i)

            Cg = CoinGeckoAPI()
            prices = Cg.get_token_price(
                id = self.coinGeckoId,
                contract_addresses = tokenAdresses,
                vs_currencies = 'usd' )
        
        with open(self.priceLookupPath,'w') as PW:
            json.dump({**temp,**prices},PW,indent = 2)

        if returns:
            return {**temp,**prices}

    def pollRoutes(self, routes = [], save = True, screen = True,currentPrice = True,start = 0):
        print('polling routes ...')
        Method = 'Manual'
        if not routes:
            Method = 'Auto'
            with open(self.routePath) as RO:
                routes = json.load(RO)['Data']

        if start > 0:
            assert start < len(routes) - 2
            routes = routes[start:]

        if screen:
            routes = self.screenRoutes(routes,save = False)

        priceLookup = {}
        if currentPrice:
            priceLookup = self.lookupPrice(True)

        history = set()
        result = []
        routeLenght = len(routes)
        summary = {
            'total' : routeLenght,
            'requested' : 0,
            'polled' : 0 }

        try:
            for pos, route in enumerate(routes):
                simplifiedroute = self.simplyfy(route)
                print(f'{pos + 1} / {routeLenght}')
                if simplifiedroute[0] in history or simplifiedroute[1] in history:
                    warnings.warn(f'route {simplifiedroute[:2]} already polled!')
                    continue
                
                # self.polRoute returns a tuple of [capital,rates,Ep]
                
                for P, item in enumerate(self.pollRoute(route)):
                    capital, rates, EP = item
                    startToken = simplifiedroute[P + 2][0]['from']
                    if priceLookup:
                        USD_Value = priceLookup[self.tokens[startToken]]['usd']
                    else:
                        USD_Value = 0

                    result.append({
                        'simplyfiedRoute' : simplifiedroute[P],
                        'route' : simplifiedroute[P + 2],
                        'index' : rates[-1],
                        'capital' : capital,
                        'EP' : EP,
                        'USD Value' : USD_Value * EP
                    })

                summary['polled'] += 2
                summary['requested'] += 1

                history.add(simplifiedroute[0])
                history.add(simplifiedroute[1])

            print('Done!')
        except:
            print('failed to poll, an error occured!')
        finally:
            if result[0]['USD Value']:
                export = sorted(result, key = lambda v : v['USD Value'], reverse = True)
            else:
                export = sorted(result, key = lambda v : v['EP'], reverse = True)
                
            if save:
                routeInfo = {}
                if Method == 'Auto':
                    with open(self.routePath) as routes:
                        Info = json.load(routes)
                        routeInfo['startExchanges'] = Info['MetaData']

                with open(self.pollPath,'w') as DP:
                    json.dump(
                        {'MetaData': {
                            'time': time.ctime(),
                            'indexStopped' : pos + start,
                            'Total' : routeLenght,
                            'routeInfo' : routeInfo
                            },
                        'Data':export}, 
                        DP, indent = 2)
            else:
                return (summary,history)
              
    def screenRoutes(self,  routes, save = True):
        print('screening routes...')
        history = set()
        result = []

        for route in routes:
            simplifiedroute = self.simplyfy(route)
            if simplifiedroute[0] in history or simplifiedroute[1] in history:
                continue
            else:
                result.append(route)
                history.add(simplifiedroute[0])
                history.add(simplifiedroute[1])

        if save:
            with open(self.routePath,'w') as AR:
                json.dump(result,AR,indent = 2)  
        else:
            return result


class Aurora(Blockchain):
    def __init__(self):
        super().__init__()
        self.source = 'https://aurorascan.dev/address/'
        self.testData = Cfg.AuroraTestData
        self.exchanges = Cfg.AuroraExchanges
        self.tokens = Cfg.AuroraTokens
        self.startTokens = Cfg.AuroraStartTokens
        self.startExchanges = Cfg.AuroraStartExchanges
        self.coinGeckoId = 'aurora'
        self.headers = {}
        self.pollPath = os.path.join(self.dataPath, 'Aurora', 'pollResult.json')
        self.routePath = os.path.join(self.dataPath, 'Aurora', 'arbRoutes.json')
    
    def __repr__(self):
        return 'Aurora Blockchain'

class Arbitrum(Blockchain):
    def __init__(self):
        super().__init__()
        self.source = 'https://arbiscan.io/address/'
        self.testData = ''
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId = ''
        self.headers = {}
        self.pollPath = os.path.join(self.dataPath,'Arbitrum','pollResult.json')
        self.routePath = os.path.join(self.dataPath,'Arbitrum', 'arbRoutes.json')

    def __repr__(self):
        return 'Arbitrum Blockchain'

class BSC(Blockchain):
    def __init__(self):
        super().__init__()
        self.source = 'https://bscscan.com/address/'
        self.testData = ''
        self.exchanges = Cfg.BSCExchanges
        self.tokens = Cfg.BSCTokens
        self.startTokens = Cfg.BSCStartTokens
        self.startExchanges = Cfg.BSCStartExchanges
        self.coinGeckoId = 'binance-smart-chain'
        self.headers = {
        'User-Agent': 'PostmanRuntime/7.29.0',
        }
        self.pollPath = os.path.join(self.dataPath,'BSC', 'pollResult.json')
        self.routePath = os.path.join(self.dataPath,'BSC', 'arbRoute.json')
      
    def __repr__(self):
        return 'Binance SmartChain'


class Kovan(Blockchain):
    def __init__(self):
        super().__init__()
        self.source = ''
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId = ''
        self.headers = {}
        self.pollPath = os.path.join(self.dataPath,'Kovan','pollResult.json')
        self.routePath = os.path.join(self.dataPath,'Kovan', 'arbRoute.json')


    def __repr__(self):
        return 'Kovan Testnet' 

class Goerli(Blockchain):
    def __init__(self):
        super().__init__()
        self.source = ''
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId = ''
        self.headers = {}
        self.pollPath = os.path.join(self.dataPath,'Goerli','pollResult.json')
        self.routePath = os.path.join(self.dataPath,'Goerli', 'arbRoute.json')


    def __repr__(self):
        return 'Goerli Testnet' 
 
