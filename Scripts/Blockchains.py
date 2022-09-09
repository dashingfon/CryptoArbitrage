'''
Blockchain module containing the different blockchain implementation
'''
#The config file contains related blockchain specific information

from typing import Callable
import scripts.Config as Cfg
from scripts.utills import isTestnet, readJson, writeJson
'''
Then to import the other modules needed
'''
import time, os, warnings
import asyncio, aiohttp, aiolimiter
from bs4 import BeautifulSoup
from pycoingecko import CoinGeckoAPI 


'''
The main blockchain class other specific blockchains inherit
It contains all the methods
'''
class Blockchain:
    limiter = aiolimiter.AsyncLimiter(75,1)
    priceCache = {'__meta__' : {'limit' : 200, 'current' : 0}}

    def __init__(self, url: str):
        self.impact = 0.00075
        self.r1 = 0.997 
        self.depthLimit = 4
        self.graph = {}
        self.cache = {}
        self.arbRoutes = []
        self.headers = {'User-Agent': 'PostmanRuntime/7.29.0'}
        self.url = url
        self.dataPath = os.path.join(
            os.path.split(os.path.dirname(__file__))[0],'data')
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
                    drop = followed + [frozenset([i['to'],i['via'],path[-1]['to']])]
                    new_path = path + [i]
                    new_path[-1]['from'] = new_path[-2]['to']
                    result += self.dive(depth + 1, i['to'], goal,new_path, drop)
        
        return result

    def DLS(self,goal,exchanges):
        # implementation of depth limited search

        start = []
        result = []
        path = {'from': goal}
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
            followed = [frozenset([goal,i['to'],i['via']])]
            new_path = [{**path, **i}]
            # recursive function to search the node to the specified depth
            result += self.dive(depth + 1, i['to'],goal,new_path,followed)

        return result
           
    def getArbRoute(self, tokens = 'default', exchanges = 'all',graph = True, save = True, screen = True):
        # The method the produces and optionally saves the Arb routes

        route = []

        if graph:
            self.buildGraph()

        # add functionality to get routes from specific start exchanges

        if tokens == 'default':
            tokens = self.startTokens
        elif tokens == 'all':
            tokens = list(self.tokens.keys())

        if exchanges == 'default':
            exchanges = self.startExchanges
        elif exchanges == 'all':
            exchanges = list(self.exchanges.keys())
        
        if type(tokens) != list:
            raise ValueError('invalid token argument')
        elif type(exchanges) != list:
            raise ValueError('invalid token argument')

        for token in tokens:
            route += self.DLS(token,exchanges)

        if screen:
            route = self.screenRoutes(route)

        if save:
            writeJson(self.routePath,
                    {'MetaData': {
                        'time': time.ctime(),
                        'total' : len(route),
                        'filtered': {
                            'status' : False,
                            'value': None
                        },
                        'Exchanges' : exchanges,
                        'Tokens' : tokens,
                    },
                    'Data': route})
        else:
            return route

    @staticmethod
    def extract(content,swap):
        price = {}
        soup = BeautifulSoup(content, 'html.parser')
        
        tokensList = soup.find_all('li',class_ = 'list-custom')
        #print(tokensList)
        done1, done2, slider = False, False, 0

        while (not done1 or not done2) and slider < len(tokensList):  
            try:
                raw = tokensList[slider].find(class_ = 'list-amount').string
                rawPrice = str(raw).split()
                symbol, amount = rawPrice[1], float(rawPrice[0].replace(',',''))
                
                if symbol == swap['from'][:-8]:
                    done1 = True
                    price[swap['from']] = amount
                elif symbol == swap['to'][:-8]:
                    done2 = True
                    price[swap['to']] = amount
                else:
                    price[symbol] = amount
                
            except (ValueError, IndexError):
                print(f'Error parsing item {rawPrice}')
            finally:
                slider += 1  
        
        return price
    

    async def fetch(self, session, address):
        url = self.source + address
        attemptsAllowed = 4
        tries = 0
        done = False

        while tries < attemptsAllowed and not done:
            try:
                async with self.limiter:
                    response = session.get(url, headers = self.headers, ssl = False)

            except Exception as e:
                print(f'Error :- {e}')
                time.sleep(2)
                tries += 1
                print(f'Retring... \n{attemptsAllowed - tries} tries left')
            else:
                done = True

        return response

    async def getPrices(self, route, session):
        addr: Callable = lambda i: (self.exchanges[i['via']]['pairs'][frozenset([i['from'],i['to']])], i)
        tasks = []
    
    async def getPrice(self, session, address, swap):

        if address in self.priceCache and \
            self.priceCache[address]['expirationTime'] < time.perf_counter() and \
            self.priceCache['__meta__']['current'] < self.priceCache['__meta__']['limit']:

            price = self.priceCache[address]['content']
        else:
            async with await self.fetch(session,address) as response:
                if response.status == 200:
                    price = self.extract(await response.text(),swap)
                assert price

            if address not in self.priceCache and \
                self.priceCache['__meta__']['current'] < self.priceCache['__meta__']['limit']:
                self.priceCache['__meta__']['current'] += 1

            self.priceCache[address] = {
                'expirationTime' : time.perf_counter() + 3, 'content' : price}

            


        return price
 
    def getRate(self,price, to, fro):
        if (to not in price) or (fro not in price):
            raise ValueError('currency not in price dictionary')

        #return self.r1 * price[to] / (1 + (self.impact * self.r1)) / price[fro] 
        return self.r1 * price[to] / price[fro] 

    @staticmethod
    def cumSum(listItem):
        result = [listItem[0]]
        for i in listItem[1:]:
            result.append(i*result[-1])
        return result

    @staticmethod
    def simplyfy(route):
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

    @staticmethod
    def assemble(route):
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

    async def pollRoute(self, route, prices = []):
        rates = [[],[]]
        liquidity = []
        
        if prices:
            assert len(prices) == len(route)
        else: 
            async with aiohttp.ClientSession() as session:
                prices = [await self.getPrices(route,session)]
        
        simplified = self.simplyfy(route)
        for index, swap in enumerate(route):
            price = prices[index]
            rate = (self.getRate(price, swap['to'], swap['from']),
            self.getRate(price, swap['from'], swap['to']))

            if index == 0:
                liquidity.append(price[swap['from']])
                forward = price[swap['to']]
                rates[0].append(rate[0])
            elif index == len(route) - 1:
                rates[0].append(rate[0] * rates[0][-1])
                liquidity += [min(price[swap['from']],forward),price[swap['to']]]
            else:
                rates[0].append(rate[0] * rates[0][-1])
                liquidity.append(min(price[swap['from']],forward))
                forward = price[swap['to']]

            rates[1].insert(0,rate[1])

        least = min(liquidity)
        reverse = liquidity[::-1]
        rates[1] = [1] + self.cumSum(rates[1])
        rates[0] = [1] + rates[0]

        cap0 = least / rates[0][liquidity.index(least)] * self.impact
        cap1 = least / rates[1][reverse.index(least)] * self.impact

        return (
            [cap0,rates[0],self.simulateSwap(simplified[2],cap0,prices)],
            [cap1,rates[1],self.simulateSwap(simplified[3],cap1,prices[::-1])]
        )

    def lookupPrice(self, returns = False):
        temp = readJson(self.priceLookupPath)
        prices = {}

        if not isTestnet(self):
            tokenAdresses = list(self.tokens.values())

            Cg = CoinGeckoAPI()
            prices = Cg.get_token_price(
                id = self.coinGeckoId,
                contract_addresses = tokenAdresses,
                vs_currencies = 'usd' )

        writeJson(self.priceLookupPath,{**temp,**prices})

        if returns:
            return {**temp,**prices}

    async def getNsetCache(self,exchange,pairs,session,address,content):
        async with await self.fetch(session,address) as response:
            result = self.extract(await response.text(), content)
        assert result, f'Empty price returned, pairs - {pairs}, exchange - {exchange}'
        if exchange not in self.cache:
            self.cache[exchange] = {}
        self.cache[exchange][pairs] = result

    async def buildCache(self, session, exchanges = []):
        print('building cache ... \n')

        content, tasks = {}, []
        if not exchanges:
            exchanges = self.exchanges.keys()

        for exchange, info in self.exchanges.items():
            if exchange in exchanges:
                for pairs, address in info['pairs'].items():
                    content['from'], content['to'] = list(pairs)
                    tasks.append(self.getNsetCache(exchange,pairs,session,address,content))

        await asyncio.gather(*tasks)

    def simulateSwap(self,route,cap,prices):
        In = cap
        assert len(prices) == len(route)
        
        for index, swap in enumerate(route):
            price = prices[index]

            Out = In * self.getRate(
                price,
                swap['to'],
                swap['from']) / (1 + ((In/price[swap['from']]) * self.r1))
            In = Out
            
        return Out - cap

    async def pollRoutes(self, routes = [], save = True, screen = True,currentPrice = True, value = 1):
        routeInfo = {}
        if not routes:
            routes = readJson(self.routePath)
            routeInfo = routes['MetaData']
            routes = routes['Data']

        if screen:
            routes = self.screenRoutes(routes)

        routeLenght = len(routes)

        message = f"""

polling routes ...

filtered by :- {value}
total of :- {routeLenght}

        """
        print(message)

        if currentPrice: 
            priceLookup = self.lookupPrice(True)
        else: 
            priceLookup = readJson(self.priceLookupPath)

        history, result = set(), []
        summary = {'total' : routeLenght, 'requested' : 0, 'polled' : 0 }

        async with aiohttp.ClientSession() as sess:
            await self.buildCache(sess)
        
        print('')
        for index, route in enumerate(routes):
            print(f'route {index + 1} of {routeLenght}')
            simplifiedroute = self.simplyfy(route)
            if simplifiedroute[0] in history or simplifiedroute[1] in history:
                warnings.warn(f'route {simplifiedroute[:2]} already polled!')
                print('')
                continue
            
            try:
                prices = []
                for swap in route:
                    prices.append(self.cache[swap['via']][frozenset((swap['from'],swap['to']))])
                
                # self.polRoute returns a tuple of [capital,rates,Ep]
                
                for P, item in enumerate(await self.pollRoute(route, prices)):
                    capital, rates, EP = item
                    startToken = simplifiedroute[P + 2][0]['from']

                    if rates[-1] >= value:
                        if self.tokens[startToken] in priceLookup:
                            USD_Value = priceLookup[self.tokens[startToken]]['usd']
                        else:
                            USD_Value = 0

                        result.append({
                            'route' : simplifiedroute[P],
                            'index' : rates[-1],
                            'capital' : capital,
                            'EP' : EP,
                            'USD Value' : USD_Value * EP
                        })

                summary['polled'] += 2
                summary['requested'] += 1
                history.add(simplifiedroute[0])
                history.add(simplifiedroute[1])

            except Exception as e:
                print('failed to poll, an error occured!')
                print(e)

        print('\nDone!')
            
        
        if priceLookup:
            export = sorted(result, key = lambda v : v['USD Value'], reverse = True)
        else:
            export = sorted(result, key = lambda v : v['EP'], reverse = True)
            
        if save:
            writeJson(self.pollPath,
                    {'MetaData': {
                        'time': time.ctime(),
                        'total' : routeLenght,
                        'routeInfo' : routeInfo
                        },
                    'Data':export})
        else:
            return (summary,history)

    async def genRoutes(self, routes = [], value = 1):


        async with aiohttp.ClientSession() as sess:
            pass


    def screenRoutes(self, routes):
        
        history = set()
        result = []

        for route in routes:
            simplifiedroute = self.simplyfy(route)
            if simplifiedroute[0] not in history and simplifiedroute[1] not in history:
                result.append(route)
                history.add(simplifiedroute[0])
                history.add(simplifiedroute[1])

        return result


class Aurora(Blockchain):
    def __init__(self, url:str = 'http://127.0.0.1:8545'):
        super().__init__(url)
        self.source = 'https://aurorascan.dev/address/'
        self.testData = Cfg.AuroraTestData
        self.exchanges = Cfg.AuroraExchanges
        self.tokens = Cfg.AuroraTokens
        self.startTokens = Cfg.AuroraStartTokens
        self.startExchanges = Cfg.AuroraStartExchanges
        self.coinGeckoId = 'aurora'
        self.geckoTerminalName = 'aurora'
        self.arbAddress = ''
        self.pollPath = os.path.join(self.dataPath, 'Aurora', 'pollResult.json')
        self.routePath = os.path.join(self.dataPath, 'Aurora', 'arbRoutes.json')
    
    def __repr__(self):
        return 'Aurora Blockchain'

class Arbitrum(Blockchain):
    def __init__(self, url:str = 'http://127.0.0.1:8545'):
        super().__init__(url)
        self.source = 'https://arbiscan.io/address/'
        self.testData = ''
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId = ''
        self.geckoTerminalName = 'arbitrum'
        self.arbAddress = ''
        self.pollPath = os.path.join(self.dataPath,'Arbitrum','pollResult.json')
        self.routePath = os.path.join(self.dataPath,'Arbitrum', 'arbRoutes.json')

    def __repr__(self):
        return 'Arbitrum Blockchain'

class BSC(Blockchain):
    def __init__(self, url:str = 'http://127.0.0.1:8545'):
        super().__init__(url)
        self.source = 'https://bscscan.com/address/'
        self.testData = ''
        self.exchanges = Cfg.BSCExchanges
        self.tokens = Cfg.BSCTokens
        self.startTokens = Cfg.BSCStartTokens
        self.startExchanges = Cfg.BSCStartExchanges
        self.coinGeckoId = 'binance-smart-chain'
        self.geckoTerminalName = 'bsc'
        self.arbAddress = ''
        self.pollPath = os.path.join(self.dataPath,'BSC', 'pollResult.json')
        self.routePath = os.path.join(self.dataPath,'BSC', 'arbRoute.json')
      
    def __repr__(self):
        return 'Binance SmartChain'


class Kovan(Blockchain):
    def __init__(self, url:str = 'http://127.0.0.1:8545'):
        super().__init__(url)
        self.source = ''
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId = ''
        self.arbAddress = ''
        self.pollPath = os.path.join(self.dataPath,'Kovan','pollResult.json')
        self.routePath = os.path.join(self.dataPath,'Kovan', 'arbRoute.json')


    def __repr__(self):
        return 'Kovan Testnet' 

class Goerli(Blockchain):
    def __init__(self, url:str = 'http://127.0.0.1:8545'):
        super().__init__(url)
        self.source = ''
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId = ''
        self.arbAddress = ''
        self.pollPath = os.path.join(self.dataPath,'Goerli','pollResult.json')
        self.routePath = os.path.join(self.dataPath,'Goerli', 'arbRoute.json')


    def __repr__(self):
        return 'Goerli Testnet' 

class Fantom(Blockchain):
    def __init__(self, url:str = 'http://127.0.0.1:8545'):
        super().__init__(url)
        self.source = ''
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId = ''
        self.arbAddress = ''
        self.pollPath = os.path.join(self.dataPath,'Goerli','pollResult.json')
        self.routePath = os.path.join(self.dataPath,'Goerli', 'arbRoute.json')


    def __repr__(self):
        return 'Goerli Testnet' 
 
class Polygon(Blockchain):
    def __init__(self, url:str = 'http://127.0.0.1:8545'):
        super().__init__(url)
        self.source = ''
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId = ''
        self.arbAddress = ''
        self.pollPath = os.path.join(self.dataPath,'Polygon','pollResult.json')
        self.routePath = os.path.join(self.dataPath,'Polygon', 'arbRoute.json')

