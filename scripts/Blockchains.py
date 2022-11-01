'''
Blockchain module containing the different blockchain implementation
The main blockchain class inherits from the BaseBlockchain
which other Blockchains then inherit from
'''

from scripts import CONFIG_PATH, path
import scripts.Errors as errors
from scripts.Models import (
    Token,
    Swap,
    Via,
    Route
    )
from scripts.Utills import (
    readJson,
    writeJson,
    extractTokensFromHtml,
    buildData,
    setData,
    asyncProfiler
    )

import logging
import web3
from web3.eth import AsyncEth
import asyncio
import aiohttp
from aiolimiter import AsyncLimiter
from pycoingecko import CoinGeckoAPI
from attr import asdict


Limiter: AsyncLimiter = AsyncLimiter(max_rate=200, time_period=1)
Config: dict = readJson(CONFIG_PATH)
Price = dict[Token, int]


class Blockchain:
    '''Blockchain chain class implementation
    Must implement genRoutes according to the superclass'''

    def __init__(self, url: str = '') -> None:
        if type(self) == Blockchain:
            raise errors.CannotInitializeDirectly(
                'Blockchain class can only be used through inheritance')

        self.impact: float = 0.00075
        self.r1: float = 0.997
        self.depthLimit: int = 4
        self.graph: dict[Token, list[dict]] = {}
        self.exchanges: dict
        self.headers: dict[str, str] = {
            'User-Agent': 'PostmanRuntime/7.29.0',
            "Connection": "keep-alive"
            }
        self.dataPath: str = str(path.joinpath('data'))
        self.arbPath: str = str(
            path.joinpath('data', 'Database',
                          f'{str(self).split()[0]}_Routes.json'))
        self.priceLookupPath: str = str(path.joinpath(self.dataPath, 'PriceLookup.json'))  # noqa
        self.url: str = 'http://127.0.0.1:8545' if not url else url
        self.w3 = web3.Web3(web3.AsyncHTTPProvider(self.url,
                            request_kwargs={'timeout': 60}),
                            modules={'eth': (AsyncEth,)},
                            middlewares=[])
        self.source: str
        self.coinGeckoId: str
        self.geckoTerminalName: str
        '''
        impact: float :- the amount of price impact allowed
        r1: float :- The swap fee on dexs
        depthLimit: int :- Used to determine the longest cycle of swaps
        graph: dict :- a representation of the connected tokens across dexs
        exchanges: dict
        header: dict :- requests header
        dataPath: str :- the path to the data directory
        priceLookupPath: path to json file containing token prices
        url: blockchain endpoint url
        source: str
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
    def arbAddress(self) -> str:
        '''property to get the arbAddress'''

        chainContent = Config.get(str(self))
        if chainContent:
            if chainContent.get('arbAddress'):
                return chainContent.get('arbAddress')
        return ''

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

                Token0 = Token(pool[0][:-8],
                    web3.Web3.toChecksumAddress(tokens[pool[0]]))  # noqa E128
                Token1 = Token(pool[1][:-8],
                    web3.Web3.toChecksumAddress(tokens[pool[1]]))  # noqa E128

                temp[frozenset([Token0, Token1])] = web3.Web3.toChecksumAddress(  # noqa E501
                    addresses)

                if Token0 not in graph:
                    graph[Token0] = []
                if Token1 not in graph:
                    graph[Token1] = []

                graph[Token0].append({'to': Token1, 'via': dex})
                graph[Token1].append({'to': Token0, 'via': dex})

            pairs[dex]['pairs'] = temp

        self.graph = graph
        self.exchanges = pairs

        for key, value in self.graph.items():
            for item in value:
                if {'to': key, 'via': item['via']} not in self.graph[item['to']]:  # noqa E501
                    logging.debug(f'{key} not found in {item} list')

    def dive(self, depth: int, node: Token, goal: Token,
             path: list[Swap],
             followed: set, price: float) -> list[Route]:
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
                                       fro=path[-1].to,
                                       to=i['to'],
                                       via=Via(
                                        name=i['via'],
                                        pair=self.exchanges[i['via']]['pairs'][
                                            frozenset((path[-1].to, i['to']))
                                        ],
                                        fee=self.exchanges[i['via']]['fee'],
                                        router=self.exchanges[i['via']]['router']))]  # noqa E501

                    if i['to'] == goal:
                        result.append(Route(swaps=new_path,
                                            UsdValue=price))
                    elif depth < self.depthLimit:
                        drop = {*followed, frozenset(
                                            [i['to'], i['via'], path[-1].to])}
                        result += self.dive(
                                    depth + 1, i['to'], goal, new_path, drop, price)  # noqa E501

        return result

    def DLS(self, goal: Token, tokenPrice: float) -> list[Route]:
        '''implementation of depth limited search'''

        start = []
        result = []
        depth = 1

        if goal in self.graph:
            start = self.graph[goal]

        for i in start:
            followed = {frozenset((goal, i['to'], i['via']))}
            new_path = [Swap(fro=goal,
                             to=i['to'],
                             via=Via(name=i['via'],
                                     pair=self.exchanges[i['via']]['pairs'][
                                        frozenset((goal, i['to']))
                                     ],
                                     fee=self.exchanges[i['via']]['fee'],
                                     router=self.exchanges[i['via']]['router']
                                     ))]
            # recursive function to search the node to the specified depth
            result += self.dive(depth + 1, i['to'], goal, new_path, followed,
                                tokenPrice)

        return result

    def getArbRoute(self, tokens: dict[str, str] = {},
                    exchanges: dict = {},
                    save: bool = True,
                    screen: bool = True,
                    livePrice: float = 0) -> list | None:
        '''
        The method that produces and optionally saves the Arb routes
        '''
        self.buildGraph(tokens=tokens, exchanges=exchanges)

        prices: dict[str, dict[str, float]] = readJson(self.priceLookupPath)
        routes: list[Route] = []

        for token in self.graph:
            if livePrice:
                price = livePrice
            else:
                price = prices[token.address.lower()]['usd']

            routes += self.DLS(token, price)

        logging.info(f'{len(routes)} raw routes found')
        if screen and routes:
            routes = self.screenRoutes(routes)
            logging.info(f'{len(routes)} final routes found')

        if save:
            logging.info('saving routes...')
            writeJson(
                self.arbPath,
                [asdict(route) for route in routes]  # type: ignore
            )
            logging.info('Done!')
            return None
        else:
            return routes

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

    async def getPriceFromExplorer(self, session: aiohttp.ClientSession,
                                   addr: str,
                                   swap: set[Token]) -> dict:

        '''method to get token prices using the explorer'''
        price: Price = {}

        url = self.source + addr
        async with Limiter:
            async with session.get(url, headers=self.headers, ssl=False) as response:  # noqa E501

                if response.status == 200:
                    try:
                        price = extractTokensFromHtml(await response.text(),
                                                      swap)
                    except AssertionError:
                        logging.exception(
                            f'failed request, pairs :- {swap}')  # noqa E501
                else:
                    logging.error(
                        f'error, status code {response.status}')

        return price

    async def getPrice(self, addr: str, swap: set[Token]) -> Price:
        '''method to get the token prices from blockchain nodes'''
        price: Price = {}
        abi: list = Config['ABIs']['PairAbi']

        Contract = self.w3.eth.contract(address=addr, abi=abi)  # type: ignore
        rawPrice = await Contract.functions.getReserves().call()
        tokens = sorted(swap)
        price[tokens[0]] = rawPrice[0]
        price[tokens[1]] = rawPrice[1]

        return price

    async def fetchNset(self, cache: dict, addr: str,
                        swap: set[Token]) -> None:

        price = await self.getPrice(addr=addr, swap=swap)
        cache[addr] = price

    async def buildCache(self, routes: list[Route],
                         save: bool = False) -> dict[str, Price]:
        '''function to cache the routes'''

        cache: dict[str, Price] = {}
        uniques: dict[str, set[Token]] = {}
        tracker: set[str] = set()
        for route in routes:
            for swap in route.swaps:
                address = swap.via.pair
                if address not in tracker:
                    uniques[address] = {swap.to, swap.fro}
                    tracker.add(address)

        tasks = []
        for key, value in uniques.items():
            tasks.append(self.fetchNset(cache, key, value))

        await asyncio.gather(*tasks)

        if save:
            result = {}
            for k, v in cache.items():
                temp = {}
                for i, j in v.items():
                    temp[i.fullJoin] = j
                result[k] = temp

            cachePath = str(path.joinpath(self.dataPath, 'SampleCache.json'))
            writeJson(
                cachePath,
                result
            )
        return cache

    def screenRoutes(self, routes: list[Route]) -> list:

        history = set()
        result = []

        for route in routes:
            reverse = route.reverseSimplyfied()
            if route.simplyfied_short not in history and \
                    reverse not in history:

                result.append(route)
                history.add(route.simplyfied_short)
                history.add(reverse)

        return result


class Aurora(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__(url=url)
        self.source = 'https://aurorascan.dev/address/'
        self.coinGeckoId = 'aurora'
        self.geckoTerminalName = 'aurora'

    def __repr__(self) -> str:
        return 'Aurora Blockchain'


class Arbitrum(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__(url=url)
        self.source = 'https://arbiscan.io/address/'
        self.coinGeckoId = ''
        self.geckoTerminalName = 'arbitrum'

    def __repr__(self) -> str:
        return 'Arbitrum Blockchain'


class BSC(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__(url=url)
        self.source = 'https://bscscan.com/address/'
        self.coinGeckoId = 'binance-smart-chain'
        self.geckoTerminalName = 'bsc'

    def __repr__(self) -> str:
        return 'Binance SmartChain'


class Fantom(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__(url=url)
        self.source = ''
        self.coinGeckoId = ''
        self.geckoTerminalName = 'bsc'

    def __repr__(self) -> str:
        return 'Fantom Blockchain'


class Polygon(Blockchain):

    def __init__(self, url: str = '') -> None:
        super().__init__(url=url)
        self.source = ''
        self.coinGeckoId = ''
        self.geckoTerminalName = 'bsc'

    def __repr__(self) -> str:
        return 'Polygon Blockchain'


class Test(Blockchain):

    def __init__(self) -> None:
        super().__init__()

    def __repr__(self) -> str:
        return 'Test Chain'
