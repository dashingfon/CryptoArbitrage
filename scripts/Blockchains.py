'''
Blockchain module containing the different blockchain implementation
The main blockchain class inherits from the BaseBlockchain
which other Blockchains then inherit from
'''

from scripts import CONFIG_PATH, DATABASE_URL, path
import scripts.Errors as errors
from scripts.Models import (
    Token,
    Swap,
    Route,
    Routes,
    BaseBlockchain,
    Price,
    Spliter
    )
from scripts.Utills import (
    readJson,
    writeJson,
    extractTokensFromHtml,
    buildData,
    setData
    )
from scripts.Database import (
    SQLModel,
    create_engine,
    Session,
    select
    )
import logging
# import web3
import time
import asyncio
import aiohttp
from aiolimiter import AsyncLimiter
from pycoingecko import CoinGeckoAPI
from cache import AsyncTTL
from typing import AsyncGenerator, Callable, Optional, Any, Type


Cache: AsyncTTL = AsyncTTL(time_to_live=5, maxsize=150)
Limiter: AsyncLimiter = AsyncLimiter(max_rate=25, time_period=1)
Config: dict = readJson(CONFIG_PATH)
Engine: Any = create_engine(DATABASE_URL)


class Blockchain(BaseBlockchain):
    '''Blockchain chain class implementation
    inheriting from the Base Blockchain.
    Must implement genRoutes according to the superclass'''

    def __init__(self) -> None:
        if type(self) == Blockchain:
            raise errors.CannotInitializeDirectly(
                'Blockchain class can only be used through inheritance')
        self.impact: float = 0.00075
        self.r1: float = 0.997
        self.depthLimit: int = 4
        self.graph: dict = {}
        self.exchanges: dict
        self.arbRoutes: list
        self.headers: dict[str, str] = {
            'User-Agent': 'PostmanRuntime/7.29.0',
            "Connection": "keep-alive"
            }
        self.dataPath: str = str(path.joinpath('data'))
        self.priceLookupPath: str = str(path.joinpath(self.dataPath, 'PriceLookup.json'))  # noqa
        self.url: str = 'http://127.0.0.1:8545'
        self.tableName: str = f'{str(self)} Routes'
        self.table: Type[Routes] = type(self.tableName,
                          (Routes,),  # noqa E128
                          {'__tablename__': self.tableName},
                          table=True)
        self.source: str
        self.coinGeckoId: str
        self.geckoTerminalName: str
        '''
        impact: float :- the amount of price impact allowed
        r1: float :- The swap fee on dexs
        depthLimit: int :- Used to determine the longest cycle of swaps
        graph: dict :- a representation of the connected tokens across dexs
        arbRoutes: list :- a list of the cyclic routes
        header: dict :- requests header
        dataPath: str :- the path to the data directory
        priceLookupPath: str
        tableName: str
        table: Any
        url: str
        table: Any
        source: str
        exchanges: dict
        coinGeckoId: str
        geckoTerminalName: str
        '''

    @property
    def isSetup(self) -> bool:
        '''property to check if blockchain has been setup'''

        chainContent = Config.get(str(self))
        if chainContent:
            if chainContent.get('setup'):
                return True
        return False

    @property
    def arbAddress(self) -> Optional[str]:
        '''property to get the arbAddress'''

        chainContent = Config.get(str(self))
        if chainContent:
            if chainContent.get('arbAddress'):
                return chainContent.get('arbAddress')
        return None

    def setup(self, supportedExchanges: set[str] = set(),
              saveArtifact: bool = False,
              temp: bool = False) -> None:

        '''method to fetch all the token and pair addresses'''

        filePath = str(path.joinpath(self.dataPath, 'dataDump.json'))
        artifactPath = str(path.joinpath(self.dataPath, 'artifactDump.json'))

        buildData(blockchain=self, filePath=filePath,
                  artifactPath=artifactPath, saveArtifact=saveArtifact)
        setData(chain=self, dumpPath=filePath, temp=temp,
                supportedExchanges=supportedExchanges)

    def buildGraph(self, exchanges: dict = {}, tokens: dict = {}) -> None:
        '''
        returns the graphical representation of the connection between tokens
        '''

        graph: dict = {}
        pairs: dict = {}

        if not exchanges and not self.isSetup:
            raise errors.BlockchainNotSetup(f"{self} not setup")
        elif not exchanges:
            exchanges = Config[str(self)]['Exchanges']

        if not tokens and not self.isSetup:
            raise errors.BlockchainNotSetup(f"{self} not setup")
        elif not tokens:
            tokens = Config[str(self)]['Tokens']

        for dex, attributes in exchanges.items():
            temp: dict = {}
            pairs[dex] = attributes
            for pools, addresses in attributes['pairs'].items():
                pool = pools.split(' - ')

                Token0 = Token(pool[0][:-8], tokens[pool[0]])
                Token1 = Token(pool[1][:-8], tokens[pool[1]])

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

    def dive(self, depth: int, node: Token, goal: Token,
             path: list[Swap],
             followed: set) -> list[Route]:
        '''
        recursive function to discover tradable arb routes
        called from DLS
        '''

        result: list[Route] = []
        if depth <= self.depthLimit and node in self.graph:
            for i in self.graph[node]:
                if frozenset([i['to'], i['via'], path[-1].to]) in followed:
                    pass
                else:
                    new_path = path + [Swap(
                                       fro=i['to'], to=i['to'], via=i['via'])]
                    new_path[-1].fro = new_path[-2].to

                    if i['to'] == goal:
                        result.append(Route(swaps=new_path))
                    elif depth < self.depthLimit:
                        drop = {*followed, frozenset(
                                            [i['to'], i['via'], path[-1].to])}
                        result += self.dive(
                                    depth + 1, i['to'], goal, new_path, drop)

        return result

    def DLS(self, goal: Token,
            exchanges: list) -> list[Route]:
        '''implementation of depth limited search'''

        start = []
        result = []
        path: dict[str, Token] = {'from': goal}
        depth = 1

        if goal in self.graph:
            for i in self.graph[goal]:
                if i['via'] in exchanges:
                    start.append(i)

        for i in start:
            followed = set(frozenset([goal, i['to'], i['via']]))
            new_path = [Swap(fro=path['from'], to=i['to'], via=i['via'])]
            # recursive function to search the node to the specified depth
            result += self.dive(depth + 1, i['to'], goal, new_path, followed)

        return result

    def toDatabase(self, routes: list[Route]) -> None:
        '''method to get data from the database'''
        if routes:
            SQLModel.metadata.create_all(Engine)

            with Session(Engine) as sess:
                for route in routes:
                    sess.add(self.table.fromSwaps(route.swaps))
                sess.commit()

    def fromDatabase(self, selection: tuple, where: tuple = ()) -> list:
        '''method to save data to the database'''
        with Session(Engine) as sess:
            raw = select(*selection)

            statement = raw
            for i in where:
                statement = statement.where(i)

            return list(sess.exec(statement))

    def getArbRoute(self, tokens: Optional[list[Token]] = [],
                    exchanges: list = [],
                    graph: bool = True,
                    save: bool = True,
                    screen: bool = True) -> list | None:

        '''
        The method the produces and optionally saves the Arb routes
        '''
        if graph:
            self.buildGraph()

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

    async def pollRoute(self,
                        route: Route,
                        prices: list[Price] = [],
                        usdVal: float = 1,
                        **kwargs) -> list[Route]:
        '''calculates the index, expected profit and
        optimal capital of a list of routes'''

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
            prices = await self.getPrices(route)
        route.prices = prices

        return route.calculate(self.r1, self.impact, usdVal)

    def lookupPrice(self) -> None:
        '''
        method to lookup token price with coingecko api wrapper
        '''
        temp = readJson(self.priceLookupPath)
        prices = {}

        tokenAdresses = list(self.graph.keys())

        coinGecko = CoinGeckoAPI()
        prices = coinGecko.get_token_price(
            id=self.coinGeckoId,
            contract_addresses=tokenAdresses,
            vs_currencies='usd')

        writeJson(self.priceLookupPath, {**temp, **prices})

    async def getPrices(self, route: Route,
                        session: aiohttp.ClientSession | None = None) -> list[Price]:  # noqa E501

        '''method to get the token prices asynchronously'''

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
                                   swap: dict[str, Token | str],
                                   exchange: str) -> dict:

        '''method to get token prices using the explorer'''
        price: Price = {}

        url = self.source + addr
        async with Limiter:
            async with session.get(url, headers=self.headers, ssl=False) as response:  # noqa E501

                if response.status == 200:
                    try:
                        price = extractTokensFromHtml(await response.text(), swap)  # noqa E501
                    except AssertionError:
                        logging.exception(
                            f'failed request, exchange :- {exchange}, pairs :- {swap}')  # noqa E501
                else:
                    logging.error(
                        f'error, status code {response.status}')

        return price

    @Cache
    async def getPrice(self, addr, swap) -> Optional[dict]:
        '''method to get the token prices from blockchain nodes'''

    def convert(self, routes: list[Route]) -> list[dict]:
        '''method to serialize the routes into json'''
        result = []
        for route in routes:
            result.append(
                {
                    'route': route.simplyfied_short,
                    'EP': route.USD_Value / 1e18,
                    'USD_Value': route.EP,
                    'index': route.index,
                    'capital': route.capital / 1e18
                }
            )
        return result

    async def pollRoutes(self, routes: list[Route] = [],
                         save: bool = True, currentPrice: bool = False,
                         value: float = 1.009027027,
                         startTokens: str | None = None,
                         startExchanges: str | None = None,
                         amountOfSwaps: int | None = None) -> Optional[list]:

        if not routes:
            filters = []
            if startTokens:
                filters.append(self.table.startToken == startTokens)
            if startExchanges:
                filters.append(
                    self.table.startExchanges == startExchanges)
            if amountOfSwaps:
                filters.append(
                    self.table.amountOfSwaps == amountOfSwaps)

            routeFull = self.fromDatabase(
                (self.table.simplyfied_full,),
                tuple(filters)
            )
            routes = [Route.fromFullString(route) for route in routeFull]

        routeLenght = len(routes)

        logging.info('polling routes ...')
        logging.info(f'filtering by :- {value}')
        logging.info(f'total of :- {routeLenght}')

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
                logging.info('\n interupted, exiting')
                Done = True

        export = self.convert(sorted(result))
        if save:
            writeJson(self.dataPath,
                      {'MetaData': {
                        'time': time.ctime(),
                        'total': routeLenght
                        },
                       'Data': export})
            return None
        else:
            return export

    async def genRoutes(self, value: float,
                        routes: list[Route] = [],
                        **kwargs) -> AsyncGenerator:
        '''method to generate the profitable routes
        Keyword arguments:

        currentPrice: bool
        startTokens: str
        startExchnages: str
        amountOfSwaps: int
        '''

        if not routes:
            filters = []
            if kwargs.get('startTokens'):
                filters.append(
                    self.table.startToken == kwargs.get('startTokens'))
            if kwargs.get('startExchanges'):
                filters.append(
                    self.table.startExchanges == kwargs.get('startExchanges'
                    ))  # noqa E124
            if kwargs.get('amountOfSwaps'):
                filters.append(
                    self.table.amountOfSwaps == kwargs.get('amountOfSwaps'))

            routeFull = self.fromDatabase(
                (self.table.simplyfied_full,),
                tuple(filters)
            )
            routes = [Route.fromFullString(route) for route in routeFull]

        routes = self.screenRoutes(routes)
        subRoutes = Spliter(routes, Cache)
        routeLenght = len(routes)

        if kwargs.get('currentPrice'):
            self.lookupPrice()
        priceLookup = readJson(self.priceLookupPath)

        found = 0
        marker = 1
        Done = False

        while not Done:
            try:
                item = next(subRoutes)
                tasks = []
                for i in item:
                    marker += 1
                    UsdVal = priceLookup[i.swaps[0].fro]
                    tasks.append(asyncio.create_task(
                        self.pollRoute(route=i, usdVal=UsdVal)))

                done, pending = await asyncio.wait(tasks,
                                        return_when=asyncio.FIRST_EXCEPTION)  # noqa E128
                for p in pending:
                    p.cancel()

                results: list[Route] = []
                for res in done:
                    try:
                        results += await res
                    except Exception:
                        logging.exception('Fatal Error')
                        Done = True

            except StopIteration:
                logging.info('Done polling tasks')
                Done = True

            for route in results:
                if route.index > value:
                    found += 1
                    yield route

            logging.info(f'route {marker} of {routeLenght}, found {found}')
        logging.info('done polling routes')

    def screenRoutes(self, routes: list[Route]) -> list:

        history = set()
        result = []

        for route in routes:
            reverse = Route.toReversed(
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
        if url: self.url = url  # noqa E701
        self.source = 'https://aurorascan.dev/address/'
        self.coinGeckoId = 'aurora'
        self.geckoTerminalName = 'aurora'

    def __repr__(self):
        return 'Aurora Blockchain'


class Arbitrum(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa E701
        self.source = 'https://arbiscan.io/address/'
        self.coinGeckoId = ''
        self.geckoTerminalName = 'arbitrum'

    def __repr__(self):
        return 'Arbitrum Blockchain'


class BSC(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa E701
        self.source = 'https://bscscan.com/address/'
        self.coinGeckoId = 'binance-smart-chain'
        self.geckoTerminalName = 'bsc'

    def __repr__(self):
        return 'Binance SmartChain'


class Fantom(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa E701
        self.source = ''
        self.coinGeckoId = ''
        self.geckoTerminalName = 'bsc'

    def __repr__(self):
        return 'Fantom Blockchain'


class Polygon(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__()
        if url: self.url = url  # noqa E701
        self.source = ''
        self.coinGeckoId = ''
        self.geckoTerminalName = 'bsc'

    def __repr__(self):
        return 'Polygon Blockchain'
