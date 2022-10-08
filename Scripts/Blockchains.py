'''
Blockchain module containing the different blockchain implementation
The main blockchain class inherits from the BaseBlockchain
which other Blockchains then inherit from
'''

import scripts.Models as models
import scripts.Errors as errors
from scripts.Utills import (
    isTestnet,
    readJson,
    writeJson,
    extractTokensFromHtml
    )
from scripts.Database import (
    SQLModel,
    create_engine,
    Session,
    select
    )

import time
import os
import asyncio
import aiohttp
from aiolimiter import AsyncLimiter
from pycoingecko import CoinGeckoAPI
from cache import AsyncTTL
from typing import AsyncGenerator, Callable, Optional, Any
import logging


MAX_SIZE: int = 150
TIME_TO_LIVE: int = 5
Cache: AsyncTTL = AsyncTTL(time_to_live=TIME_TO_LIVE, maxsize=MAX_SIZE)
Limiter: AsyncLimiter = AsyncLimiter(25, 1)
Config: dict = readJson('Config.json')

Price = dict[models.Token, float]
GetRate = Callable[[Price, models.Token, models.Token], float]


class Blockchain(models.BaseBlockchain):
    '''Blockchain chain class implementing from Base Blockchain'''

    def __init__(self) -> None:

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
        self.getRate: GetRate = lambda price, to, fro: self.r1 * price[to] / price[fro]  # noqa
        # return self.r1 * price[to]/(1 + (self.impact * self.r1)) / price[fro]

        self.url: str = 'http://127.0.0.1:8545'
        self.databaseUrl: str
        self.engine: Any
        self.source: str
        self.exchanges: dict
        self.startTokens = None
        self.startExchanges = None
        self.coinGeckoId: str
        self.geckoTerminalName: str
        self.arbAddress: str

        '''
        impact: float :- the amount of price impact allowed
        r1: float :- The swap fee on dexs
        depthLimit: int :- Used to determine the longest cycle of swaps
        graph: dict :- a representation of the connected tokens across dexs
        arbRoutes: list :- a list of the cyclic routes
        header: dict :- requests header
        url: str :- blockchain node url
        dataPath: str :- the path to the data directory
        priceLookupPath: str
        getRate: GetRate
        url: str
        databaseUrl: str
        engine: Any
        source: str
        exchanges: dict
        startTokens = None
        startExchanges = None
        coinGeckoId: str
        geckoTerminalName: str
        arbAddress: str
        '''

    @property
    def isSetup(self):
        pass

    def setup(self) -> None:
        pass

    def buildGraph(self, exchanges: dict = {}, tokens: dict = {}) -> None:
        '''
        The method to find the connections between the tokens
        '''
        graph: dict = {}
        pairs: dict = {}

        if not exchanges:
            exchanges = Config[str(self)]['Exchanges']
        if not tokens:
            tokens = Config[str(self)]['Tokens']

        for dex, attributes in exchanges.items():
            temp: dict = {}
            pairs[dex] = attributes
            for pools, addresses in attributes['pairs'].items():
                pool = pools.split(' - ')

                Token0 = models.Token(pool[0][:-8], tokens[pool[0]])
                Token1 = models.Token(pool[1][:-8], tokens[pool[1]])

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

    def dive(self, depth: int, node: models.Token, goal: models.Token,
             path: list[dict[str, models.Token | str]],
             followed: list) -> list[Optional[models.Route]]:
        '''
        recursive function to discover tradable arb routes
        called from DLS
        '''

        result: list[Optional[models.Route]] = []
        if depth <= self.depthLimit and node in self.graph:
            for i in self.graph[node]:
                if frozenset([i['to'], i['via'], path[-1]['to']]) in followed:
                    pass
                elif i['to'] == goal:
                    new_path = path + [i]
                    new_path[-1]['from'] = new_path[-2]['to']
                    result.append(models.Route(swaps=new_path))
                elif depth < self.depthLimit:
                    drop = followed + [frozenset(
                                        [i['to'], i['via'], path[-1]['to']])]
                    new_path = path + [i]
                    new_path[-1]['from'] = new_path[-2]['to']
                    result += self.dive(
                                depth + 1, i['to'], goal, new_path, drop)

        return result

    def DLS(self, goal: models.Token,
            exchanges: list) -> list[Optional[models.Route]]:
        '''implementation of depth limited search'''

        start = []
        result = []
        path: dict[str, models.Token | str] = {'from': goal}
        depth = 1

        if goal in self.graph:
            for i in self.graph[goal]:
                if i['via'] in exchanges:
                    start.append(i)

        for i in start:
            followed = [frozenset([goal, i['to'], i['via']])]
            new_path = [{**path, **i}]
            # recursive function to search the node to the specified depth
            result += self.dive(depth + 1, i['to'], goal, new_path, followed)

        return result

    def toDatabase(self, routes: list[Optional[models.Route]]) -> None:
        if routes:
            SQLModel.metadata.create_all(self.engine)

            with Session(self.engine) as sess:
                for i in routes:
                    sess.add(models.Routes.fromString(i.simplyfied))
                sess.commit()

    def fromDatabase(self, selection: tuple, *where: tuple) -> list:
        with Session(self.engine) as sess:
            raw = select(*selection)

            for i in where:
                statement = raw.where(i)
            if not where:
                statement = raw

            return list(sess.exec(statement))

    def getArbRoute(self, tokens: Optional[list[models.Token]] = [],
                    exchanges: list = [],
                    graph: bool = True,
                    save: bool = True,
                    screen: bool = True) -> list | None:

        '''
        The method the produces and optionally saves the Arb routes
        '''
        if graph:
            self.buildGraph()

        # add functionality to get routes from specific start exchanges

        if not tokens:
            tokens = list(self.graph.keys())
        if not exchanges:
            exchanges = list(self.exchanges.keys())

        routes = []
        for token in tokens:
            routes += self.DLS(token, exchanges)

        if screen and routes:
            routes = self.screenRoutes(routes)

        if save:
            self.toDatabase(routes=routes)
            return None
        else:
            return routes

    @staticmethod
    def cumSum(listItem: list) -> list:
        result = [listItem[0]]
        for i in listItem[1:]:
            result.append(i*result[-1])
        return result

    async def pollRoute(self,
                        route: models.Route,
                        prices=[],
                        **kwargs) -> tuple[list[Any], list[Any]]:

        rates: list[list[float]] = [[], []]
        liquidity = []
        session = kwargs.get('session')
        mode = kwargs.get('mode')

        if prices:
            assert len(prices) == len(route.swaps)

        elif mode == 'fromExplorer':
            if type(session) == aiohttp.ClientSession:
                prices = await self.getPrices(route, session)
            else:
                raise errors.InvalidSession(
                    f'Expected type ClientSession, got type {type(session)}'
                )
        else:
            prices = await self.getPrices(route, None)

        for index, swap in enumerate(route.swaps):
            price = prices[index]
            rate = (self.getRate(price, swap['to'], swap['from']),
                    self.getRate(price, swap['from'], swap['to']))

            if index == 0:
                liquidity.append(price[swap['from']])
                forward = price[swap['to']]
                rates[0].append(rate[0])
            elif index == len(route.swaps) - 1:
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
            tokenAdresses = list(self.graph.keys())

            coinGecko = CoinGeckoAPI()
            prices = coinGecko.get_token_price(
                id=self.coinGeckoId,
                contract_addresses=tokenAdresses,
                vs_currencies='usd')

        writeJson(self.priceLookupPath, {**temp, **prices})

        if returns:
            return {**temp, **prices}
        return None

    async def getPrices(self, route: models.Route,
                        session: aiohttp.ClientSession | None = None) -> list:

        form: Callable[[Any], list] = lambda i: [self.exchanges[i['via']]['pairs'][frozenset([i['from'], i['to']])], i, i['via']]  # noqa: E501
        tasks = []
        if session:
            for i in route.swaps:
                tasks.append(asyncio.create_task(
                    self.getPriceFromExplorer(session, *form(i))
                ))
        else:
            for i in route.swaps:
                tasks.append(asyncio.create_task(
                    self.getPrice(*form(i)[:2])
                ))

        return await asyncio.gather(*tasks)

    @Cache
    async def getPriceFromExplorer(self, session: aiohttp.ClientSession,
                                   addr: str,
                                   swap: dict[str, models.Token | str],
                                   exchange: str) -> Optional[dict]:

        price: Optional[dict[str, str]] = {}

        url = self.source + addr
        async with Limiter:
            async with session.get(url, headers=self.headers, ssl=False) as response:  # noqa

                if response.status == 200:
                    price = extractTokensFromHtml(await response.text(), swap)
                else:
                    print(f'failed request, exchange :- {exchange}, pairs :- {swap}')  # noqa

        return price

    @Cache
    async def getPrice(self, addr, swap) -> Optional[dict]:
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

    async def pollRoutes(self, routes: list[Optional[models.Route]] = [],
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

        Done = False

        while not Done:
            try:
                result.append(await anext(routesGen))
            except StopAsyncIteration:
                Done = True
            except KeyboardInterrupt:
                print('\n interupted, exiting and saving')
                Done = True

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

    async def genRoutes(self, value: float,
                        routes: Optional[list[models.Route]] = [],
                        **kwargs: dict) -> AsyncGenerator:

        if not routes:
            routes = readJson(self.routePath)['Data']

        routes = self.screenRoutes(routes)
        subRoutes = models.Spliter(routes, Cache)
        routeLenght = len(routes)

        if kwargs.get('currentPrice'):
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
                            logging.exception('Error polling route')
                            Done = True
                        except Exception:
                            logging.exception('Fatal Error')
                            Done = True

                except StopIteration:
                    logging.info('Done polling tasks')
                    Done = True

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

                            converted: bool | None = kwargs.get('converted')
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

    def screenRoutes(self, routes: list[models.Route]) -> list:

        history = set()
        result = []

        for route in routes:
            reverse = models.Route.toReversed(
                items=route.swaps,
                prices=route.prices
            )
            if route.simplyfied_short not in history and \
                    reverse.simplyfied_short not in history:

                result.append(route)
                history.add(route.simplyfied_short)
                history.add(reverse.simplyfied_short)

        return result


class Aurora(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa

        self.source = 'https://aurorascan.dev/address/'
        self.coinGeckoId = 'aurora'
        self.geckoTerminalName = 'aurora'
        self.arbAddress = ''

    def __repr__(self):
        return 'Aurora Blockchain'


class Arbitrum(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa

        self.source = 'https://arbiscan.io/address/'
        self.databaseUrl: str = f'sqlite:///{os.path.join(self.dataPath, str(self))}.db' # noqa
        self.engine: Any = create_engine(self.databaseUrl, echo=True)
        self.coinGeckoId = ''
        self.geckoTerminalName = 'arbitrum'
        self.arbAddress = ''

    def __repr__(self):
        return 'Arbitrum Blockchain'


class BSC(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa
        self.databaseUrl: str = f'sqlite:///{os.path.join(self.dataPath, str(self))}.db' # noqa
        self.engine: Any = create_engine(self.databaseUrl, echo=True)
        self.source = 'https://bscscan.com/address/'
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
        self.coinGeckoId = ''
        self.arbAddress = ''

    def __repr__(self):
        return 'Kovan Testnet'


class Goerli(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa

        self.source = ''
        self.coinGeckoId = ''
        self.arbAddress = ''

    def __repr__(self):
        return 'Goerli Testnet'


class Fantom(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa

        self.source = ''
        self.databaseUrl: str = f'sqlite:///{os.path.join(self.dataPath, str(self))}' # noqa
        self.engine: Any = create_engine(self.databaseUrl, echo=True)
        self.coinGeckoId = ''
        self.arbAddress = ''

    def __repr__(self):
        return 'Goerli Testnet'


class Polygon(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa

        self.source = ''
        self.databaseUrl: str = f'sqlite:///{os.path.join(self.dataPath, str(self))}' # noqa
        self.engine: Any = create_engine(self.databaseUrl, echo=True)
        self.coinGeckoId = ''
        self.arbAddress = ''
