'''
Blockchain module containing the different blockchain implementation
The main blockchain class inherits from the BaseBlockchain
which other Blockchains then inherit from
'''
  
import scripts.Errors as errors
from scripts.Utills import isTestnet, readJson, writeJson
import scripts.Models as models
from scripts.Database import SQLModel, create_engine, Session, select

import time
import os
import asyncio
import aiohttp
from aiolimiter import AsyncLimiter
from bs4 import BeautifulSoup
from pycoingecko import CoinGeckoAPI
from cache import AsyncTTL
from typing import AsyncGenerator, Callable, Optional, Any
import logging


MAX_SIZE: int = 150
TIME_TO_LIVE: int = 5
Cache: AsyncTTL = AsyncTTL(time_to_live=TIME_TO_LIVE, maxsize=MAX_SIZE)
Limiter: AsyncLimiter = AsyncLimiter(25, 1)
Config: dict = readJson('Config.json')


class Blockchain(models.BaseBlockchain):
    '''Blockchain chain class implementing from Base Blockchain'''

    def __init__(self) -> None:
        '''
        impact - the amount of price impact allowed
        r1 - The swap fee on dexs
        depthLimit - Used to determine the longest cycle of swaps
        graph - a representation of the connected tokens across dexs
        arbRoutes - a list of the cyclic routes
        header - requests header
        url - blockchain node url
        dataPath - the path to the data directory
        '''
        self.impact: float = 0.00075
        self.r1: float = 0.997
        self.depthLimit: int = 4
        self.graph: dict = {}
        self.arbRoutes: list = []
        self.headers: dict[str, str] = {
            'User-Agent': 'PostmanRuntime/7.29.0',
            "Connection": "keep-alive"
            }

        self.dataPath: str = os.path.join(
            os.path.split(os.path.dirname(__file__))[0], 'data')
        self.priceLookupPath: str = os.path.join(self.dataPath, 'PriceLookup.json')  # noqa
        self.url: str = 'http://127.0.0.1:8545'

        self.databaseUrl: str = f'sqlite:///{os.path.join(self.dataPath, str(self))}' # noqa
        self.engine: Any = create_engine(self.databaseUrl, echo=True)
        self.source: str
        self.exchanges: dict
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId: str
        self.geckoTerminalName: str
        self.arbAddress: str

    def buildGraph(self) -> None:
        '''
        The method to find the connections between the tokens
        '''
        graph: dict = {}
        pairs: dict = {}

        exchanges: dict = Config[str(self)]['Exchanges']
        tokens: dict = Config[str(self)]['Tokens']

        for dex, attributes in exchanges.items():
            temp: dict = {}
            pairs[dex] = attributes
            for pools, addresses in attributes['pairs'].items():
                pool = pools.split(' - ')

                Token0 = models.Token(pool[0][-8:],
                                      tokens[pool[0][-8:]], pool[0])
                Token1 = models.Token(pool[1][-8:],
                                      tokens[pool[1][-8:]], pool[1])
                temp[frozenset([Token0, Token1])] = addresses

                if Token0 not in graph:
                    graph[Token0] = []
                if Token1 not in graph:
                    graph[Token1] = []

                graph[Token0].append({'to': Token1, 'via': dex})
                graph[Token1].append({'to': Token0, 'via': dex})

            pairs[dex]['pairs'] = temp

        self.graph = graph
        self.exchanges = pairs

    def dive(self, depth: int, node: models.Token,
             goal: models.Token, path: list[dict],
             followed: list) -> list:
        '''
        recursive function to discover tradable arb routes
        called from DLS
        '''

        result = []
        if depth <= self.depthLimit and node in self.graph:
            for i in self.graph[node]:
                if frozenset([i['to'], i['via'], path[-1]['to']]) in followed:
                    pass
                elif i['to'] == goal:
                    new_path = path + [i]
                    new_path[-1]['from'] = new_path[-2]['to']
                    result.append(new_path)
                elif depth < self.depthLimit:
                    drop = followed + [frozenset(
                                        [i['to'], i['via'], path[-1]['to']])]
                    new_path = path + [i]
                    new_path[-1]['from'] = new_path[-2]['to']
                    result += self.dive(
                                depth + 1, i['to'], goal, new_path, drop)

        return result

    def DLS(self, goal, exchanges) -> list:
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
            followed = [frozenset([goal, i['to'], i['via']])]
            new_path = [{**path, **i}]
            # recursive function to search the node to the specified depth
            result += self.dive(depth + 1, i['to'], goal, new_path, followed)

        return result

    def routesToDatabase(self, routes: list[models.Route]):
        SQLModel.metadata.create_all(self.engine)

        with Session(self.engine) as sess:
            for i in routes:
                sess.add(models.Routes.fromString(i.simplyfied))
            sess.commit()

    def routesFromDatabase(self, selection, where):
        pass

    def getArbRoute(self, tokens: list[models.Token] = [],
                    exchanges: list = [],
                    graph=True, save=True, screen=True) -> Optional[list]:

        '''
        The method the produces and optionally saves the Arb routes
        '''

        routes = []

        if graph:
            self.buildGraph()

        # add functionality to get routes from specific start exchanges

        if not tokens:
            tokens = list(self.graph.keys())
        else:
            raise errors.InvalidTokensArgument(
                f'invalid token argument {tokens}')

        if not exchanges:
            exchanges = list(self.exchanges.keys())
        else:
            raise errors.InvalidExchangesArgument(
                f'invalid exchange argument {exchanges}')

        for token in tokens:
            routes += self.DLS(token, exchanges)

        if screen:
            routes = self.screenRoutes(routes)

        if save:
            self.routesToDatabase(routes=routes)
        else:
            return routes

    def getRate(self, price, to, fro) -> float:
        if (to not in price) or (fro not in price):
            raise errors.IncompletePrice(
                f'token {to} and {fro} not in {price}')

        # return self.r1 * price[to]/(1 + (self.impact * self.r1)) / price[fro]
        return self.r1 * price[to] / price[fro]

    @staticmethod
    def cumSum(listItem: list) -> list:
        result = [listItem[0]]
        for i in listItem[1:]:
            result.append(i*result[-1])
        return result


    async def pollRoute(self, route, session,
                        prices=[]) -> tuple[list[Any], list[Any]]:

        rates = [[], []]
        liquidity = []

        if prices:
            assert len(prices) == len(route)
        else:
            prices = await self.getPrices(route, session)

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
                liquidity += [
                    min(price[swap['from']], forward), price[swap['to']]]
            else:
                rates[0].append(rate[0] * rates[0][-1])
                liquidity.append(min(price[swap['from']], forward))
                forward = price[swap['to']]

            rates[1].insert(0, rate[1])

        least = min(liquidity)
        reverse = liquidity[::-1]
        rates[1] = [1] + self.cumSum(rates[1])
        rates[0] = [1] + rates[0]

        cap0 = least / rates[0][liquidity.index(least)] * self.impact
        cap1 = least / rates[1][reverse.index(least)] * self.impact

        return (
            [cap0, rates[0], self.simulateSwap(simplified[2], cap0, prices)],
            [cap1, rates[1], self.simulateSwap(simplified[3], cap1, prices[::-1])]  # noqa: E501
        )

    def lookupPrice(self, returns=False) -> Optional[dict]:
        temp = readJson(self.priceLookupPath)
        prices = {}

        if not isTestnet(self):
            tokenAdresses = list(self.tokens.values())

            coinGecko = CoinGeckoAPI()
            prices = coinGecko.get_token_price(
                id=self.coinGeckoId,
                contract_addresses=tokenAdresses,
                vs_currencies='usd')

        writeJson(self.priceLookupPath, {**temp, **prices})

        if returns:
            return {**temp, **prices}

    @staticmethod
    def extract(content, tokens):
        assert content, 'Empty content returned'
        assert tokens, 'Empty tokens returned'

        price = {}
        soup = BeautifulSoup(content, 'html.parser')

        tokensList = soup.find_all('li', class_='list-custom')
        # print(tokensList)
        done1, done2, slider = False, False, 0

        while (not done1 or not done2) and slider < len(tokensList):
            try:
                raw = tokensList[slider].find(class_='list-amount').string
                rawPrice = str(raw).split()
                symbol = rawPrice[1]
                amount = float(rawPrice[0].replace(',', ''))

                if symbol == tokens['from'][:-8]:
                    done1 = True
                    price[tokens['from']] = amount
                elif symbol == tokens['to'][:-8]:
                    done2 = True
                    price[tokens['to']] = amount

            except (IndexError, ValueError) as e:
                print(f'Error parsing item {raw}, error :- {e}')

            except AttributeError as e:
                msg = tokensList[slider].find(class_='list-amount')
                print(f"Error parsing item {msg}, error :- {e}")

            finally:
                slider += 1

        assert len(price) == 2, f'price :- {price}\n content :- {content}\n'
        return price

    async def getPrices(self, route, session) -> list:
        form: Callable[[Any], Any] = lambda i: [self.exchanges[i['via']]['pairs'][frozenset([i['from'], i['to']])], i, i['via']]  # noqa: E501
        tasks = [asyncio.create_task(self.getPrice(session, *form(i))) for i in route]  # noqa: E501
        return await asyncio.gather(*tasks)

    @Cache
    async def getPrice(self, session, addr, swap, exchange) -> Optional[dict]:
        retries: int = 3
        price: Optional[dict[str, str]] = {}
        Done: bool = False

        while retries > 0 and not Done:
            try:
                url = self.source + addr
                async with Limiter:
                    async with session.get(url, headers=self.headers, ssl=False) as response:  # noqa
                        if response.status == 200:
                            price = self.extract(await response.text(), swap)
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
            raise errors.ErrorExtractingPrice(
                'failed to get the price')

        return price

    @Cache
    async def getPrice2(self, addr, swap) -> Optional[dict]:
        pass

    def simulateSwap(self, route, cap, prices) -> float:
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

    async def pollRoutes(self, routes: list = [],
                         save: bool = True, currentPrice: bool = False,
                         value: float = 1.009027027) -> Optional[list]:

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
        routesGen = self.genRoutes(routes=routes, value=value,
                                   currentPrice=currentPrice)

        while True:
            try:
                result.append(await anext(routesGen))
            except StopAsyncIteration:
                break
            except KeyboardInterrupt:
                print('\n interupted, exiting and saving')
            finally:
                export = sorted(result, key=lambda v: v['USD Value'],
                                reverse=True)
            if save:
                writeJson(self.pollPath,
                          {'MetaData': {
                            'time': time.ctime(),
                            'total': routeLenght,
                            'routeInfo': routeInfo
                            },
                           'Data': export})
            else:
                return export

    async def genRoutes(self, routes: Optional[list[models.Route]] = [],
                        value: float = 1.009027027,
                        converted: bool = False,
                        currentPrice: bool = False) -> AsyncGenerator:

        if not routes:
            routes = readJson(self.routePath)['Data']

        routes = self.screenRoutes(routes)
        subRoutes = models.Spliter(routes, Cache)
        routeLenght = len(routes)

        if not currentPrice:
            priceLookup = readJson(self.priceLookupPath)
        else:
            priceLookup = self.lookupPrice(returns=True)

        found = 0
        async with aiohttp.ClientSession() as sess:
            marker = 1
            Done = False

            while not Done:
                try:
                    item = next(subRoutes)
                    SimpRoutes = []
                    tasks = []
                    '''tasks = [asyncio.create_task(
                            self.pollRoute(i, sess)) for i in item]'''
                    for i in item:
                        SimpRoutes.append(self.simplyfy(i))
                        tasks.append(asyncio.create_task(
                            self.pollRoute(i, sess)))

                    done, pending = await asyncio.wait(tasks,
                                                       return_when=asyncio.FIRST_EXCEPTION)
                    for p in pending:
                        p.cancel()

                    results = []
                    for res in done:
                        try:
                            results.append(await res)
                        except AssertionError:
                            log.exception('Error polling route')
                            Done = True

                except StopIteration:
                    log.info('Done polling tasks')
                    break

                for Pos, result in enumerate(results):
                    for pos, item in enumerate(result):
                        capital, rates, EP = item
                        startToken = SimpRoutes[Pos][pos + 2][0]['from']
                        if rates[-1] >= value:
                            found += 1
                            if self.tokens[startToken] in priceLookup:
                                USD_Value = priceLookup[
                                    self.tokens[startToken]]['usd']
                            else:
                                USD_Value = 0

                            yield {
                                'route': SimpRoutes[Pos][pos + 2],
                                'index': rates[-1],
                                'capital': capital if not converted else capital * 1e18,  # noqa: E501
                                'simplified': SimpRoutes[Pos][pos],
                                'EP': EP if not converted else EP * 1e18,
                                'USD Value': USD_Value,
                            }
                    marker += 1

                print(f'                           found {found}', end='\r')
                print(f'route {marker} of {routeLenght}', end='\r')

    def screenRoutes(self, routes) -> list:

        history = set()
        result = []

        for route in routes:
            simplifiedroute = self.simplyfy(route)
            if simplifiedroute[0] not in history and \
                    simplifiedroute[1] not in history:

                result.append(route)
                history.add(simplifiedroute[0])
                history.add(simplifiedroute[1])

        return result


class Aurora(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa

        self.source = 'https://aurorascan.dev/address/'
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

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa

        self.source = 'https://arbiscan.io/address/'
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId = ''
        self.geckoTerminalName = 'arbitrum'
        self.arbAddress = ''

    def __repr__(self):
        return 'Arbitrum Blockchain'


class BSC(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa

        self.source = 'https://bscscan.com/address/'
        self.exchanges = Cfg.BSCExchanges
        self.tokens = Cfg.BSCTokens
        self.startTokens = Cfg.BSCStartTokens
        self.startExchanges = Cfg.BSCStartExchanges
        self.coinGeckoId = 'binance-smart-chain'
        self.geckoTerminalName = 'bsc'
        self.arbAddress = ''

    def __repr__(self):
        return 'Binance SmartChain'


class Kovan(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa

        self.source = ''
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId = ''
        self.arbAddress = ''

    def __repr__(self):
        return 'Kovan Testnet'


class Goerli(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa

        self.source = ''
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId = ''
        self.arbAddress = ''

    def __repr__(self):
        return 'Goerli Testnet'


class Fantom(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa

        self.source = ''
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId = ''
        self.arbAddress = ''

    def __repr__(self):
        return 'Goerli Testnet'


class Polygon(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa

        self.source = ''
        self.exchanges = None
        self.tokens = None
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId = ''
        self.arbAddress = ''

