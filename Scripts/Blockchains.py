'''
Blockchain module containing the different blockchain implementation
'''
#The config file contains related blockchain specific information

from typing import Callable
import scripts.Config as Cfg
from scripts.utills import isTestnet, readJson, writeJson, split_list

'''
Then to import the other modules needed
'''
import time, os, warnings
import asyncio
import aiohttp
from aiolimiter import AsyncLimiter
from bs4 import BeautifulSoup
from pycoingecko import CoinGeckoAPI 
from cache import AsyncTTL


'''
The main blockchain class other specific blockchains inherit
It contains all the methods
'''

class Blockchain:
    limiter: AsyncLimiter = AsyncLimiter(25,1)

    def __init__(self, url: str):
        self.impact = 0.00075
        self.r1 = 0.997 
        self.depthLimit = 4
        self.graph = {}
        self.arbRoutes = []
        self.headers = {
            'User-Agent': 'PostmanRuntime/7.29.0',
            "Connection": "keep-alive"
            }
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
                        'Exchanges' : exchanges,
                        'Tokens' : tokens,
                    },
                    'Data': route})
        else:
            return route


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
        result = [f"{route[0]['from']} {route[0]['to']} {route[0]['via']}"]
        _result = [f"{route[0]['to']} {route[0]['from']} {route[0]['via']}"]
        reverseRoute = [{
            'from' : route[0]['to'], 'to' :  route[0]['from'], 'via' : route[0]['via']
        }]

        for j in route[1:]:
            result.append(f"{j['from']} {j['to']} {j['via']}")
            _result.insert(0,f"{j['to']} {j['from']} {j['via']}")
            reverseRoute.insert(0,{
            'from' : j['to'], 'to' :  j['from'], 'via' : j['via']
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


    async def pollRoute(self, route, session, prices = []):
        rates = [[],[]]
        liquidity = []
        
        if prices:
            assert len(prices) == len(route)
        else: 
            prices = await self.getPrices(route,session)
        
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

            coinGecko = CoinGeckoAPI()
            prices = coinGecko.get_token_price(
                id = self.coinGeckoId,
                contract_addresses = tokenAdresses,
                vs_currencies = 'usd' )

        writeJson(self.priceLookupPath,{**temp,**prices})

        if returns:
            return {**temp,**prices}


    @staticmethod
    def extract(content,tokens):
        assert content, 'Empty content returned'
        assert tokens, 'Empty tokens returned'
        
        price = {}
        soup = BeautifulSoup(content, 'html.parser')
        
        tokensList = soup.find_all('li', class_ = 'list-custom')
        #print(tokensList)
        done1, done2, slider = False, False, 0

        while (not done1 or not done2) and slider < len(tokensList):  
            try:
                raw = tokensList[slider].find(class_ = 'list-amount').string
                rawPrice = str(raw).split()
                symbol, amount = rawPrice[1], float(rawPrice[0].replace(',',''))
                
                if symbol == tokens['from'][:-8]:
                    done1 = True
                    price[tokens['from']] = amount
                elif symbol == tokens['to'][:-8]:
                    done2 = True
                    price[tokens['to']] = amount
                
            except (IndexError, ValueError) as e:
                print(f'Error parsing item {raw}, error :- {e}')

            except AttributeError as e:
                print(f"Error parsing item {tokensList[slider].find(class_ = 'list-amount')}, error :- {e}")

            finally:
                slider += 1  
        
        assert len(price) == 2, f'price :- {price}\n content :- {content}\n'
        return price
    

    async def fetch(self, session, addr):
        url = self.source + addr
        async with self.limiter:
            return session.get(url, headers = self.headers, ssl = False)


    async def getPrices(self, route, session):
        form: Callable = lambda i: [self.exchanges[i['via']]['pairs'][frozenset([i['from'],i['to']])], i, i['via']]
        tasks = [asyncio.create_task(self.getPrice(session,*form(i))) for i in route]
        return await asyncio.gather(*tasks)


    @AsyncTTL(time_to_live = 5, maxsize = 200)
    async def getPrice(self, session, addr, swap, exchange):
        retries: int = 3
        price: dict[str, str] = {}
        Done: bool = False

        while retries > 0 and not Done:
            try:
                async with await self.fetch(session,addr) as response:
                    if response.status == 200:
                        price = self.extract(await response.text(),swap)
                    else:
                        print(f'failed request, exchange :- {exchange}, pairs :- {swap}')
                        break
            except aiohttp.ServerDisconnectedError as e:
                print(f"Oops, the server connection was dropped before we finished :- {e}")
                await asyncio.sleep(1)
                retries -= 1
            except aiohttp.ClientConnectionError as e:
                print(f"Oops, the connection was dropped before we finished :- {e}")
                await asyncio.sleep(1)
                retries -= 1 
            except aiohttp.ClientError as e:
                print(f"Oops, something else went wrong with the request :- {e}")
                await asyncio.sleep(1)
                retries -= 1
            else:
                Done = True

        if not Done: 
            raise RuntimeError('failed to get the price')
        
        return price


    def simulateSwap(self, route, cap, prices):
        In = cap
        assert len(prices) == len(route), 'unequal route and prices'
        
        for index, swap in enumerate(route):
            price = prices[index]

            Out = In * self.getRate(
                price,
                swap['to'],
                swap['from']) / (1 + ((In/price[swap['from']]) * self.r1))
            In = Out
            
        return Out - cap


    async def pollRoutes(self, routes = [], save = True, currentPrice = False, 
        value = 1.009027027):

        routeInfo = {}
        if not routes:
            routes = readJson(self.routePath)
            routeInfo = routes['MetaData']
            routes = routes['Data']
        routeLenght = len(routes)

        message = f"""
polling routes ...

filtering by :- {value}
total of :- {routeLenght}

        """
        print(message)
        result = []
        routesGen = self.genRoutes(value, routes, currentPrice = currentPrice)

        try:
            async for item in routesGen:
                result.append(item)
        except KeyboardInterrupt:
            print('\n interupted, exiting and saving')
        finally:
            export = sorted(result, key = lambda v : v['USD Value'], reverse = True)
            if save:
                writeJson(self.pollPath,
                        {'MetaData': {
                            'time': time.ctime(),
                            'total' : routeLenght,
                            'routeInfo' : routeInfo
                            },
                        'Data':export})
            else: return export
 

    async def genRoutes(self, value, routes: list[dict[str,str]] = [], converted: bool = False, 
        wait: int = 10, currentPrice: bool = False, batch: int = 50):
 
        if not routes:
            routes = readJson(self.routePath)['Data']

        routes = self.screenRoutes(routes)
        subRoutes = split_list(routes, batch)
        routeLenght = len(routes)

        if not currentPrice:
            priceLookup = readJson(self.priceLookupPath)
        else:
            priceLookup = self.lookupPrice(returns = True)

        found = 0
        async with aiohttp.ClientSession() as sess:
            marker = 1
            for item in subRoutes:
                try:
                    SimpRoutes = []
                    tasks = []
                    for i in item:
                        SimpRoutes.append(self.simplyfy(i))
                        tasks.append(asyncio.create_task(self.pollRoute(i, sess)))
                    results = await asyncio.gather(*tasks)

                except AssertionError as e:
                    print(f'AssertionError \n{e}')
                    print('Host rate limit reached, batch size probably too big')
                    print("skipping routes")
                    continue
                

                for Pos, result in enumerate(results):
                    for pos, item in enumerate(result):
                        capital, rates, EP = item
                        startToken = SimpRoutes[Pos][pos + 2][0]['from']
                        if rates[-1] >= value:
                            found += 1
                            if self.tokens[startToken] in priceLookup:
                                USD_Value = priceLookup[self.tokens[startToken]]['usd']
                            else:
                                USD_Value = 0

                            yield {
                                'route' : SimpRoutes[Pos][pos + 2],
                                'index' : rates[-1],
                                'capital' : capital if not converted else capital * 1e18,
                                'simplified' : SimpRoutes[Pos][pos],
                                'EP' : EP if not converted else EP * 1e18, 
                                'USD Value' : USD_Value,
                            }

                print(f'                           found {found}', end = '\r')
                step = marker * batch if marker * batch < routeLenght else routeLenght 
                print(f'route {step} of {routeLenght}', end = '\r')
        

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
    def __init__(self, url: str = 'http://127.0.0.1:8545'):
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

