import scripts.Blockchains as Blc
from scripts.Utills import readJson
from scripts import CONFIG_PATH
import pytest

Data_Available = 0
Chain = 'Aurora'


def getChain():

    if Chain == 'Aurora':
        return Blc.Aurora()
    elif Chain == ' BSC':
        return Blc.BSC()
    else:
        raise ValueError('Invalid Chain Argument')


CHAIN = getChain()

EXCHANGES = CHAIN.testData['EXCHANGES']
GRAPH = CHAIN.testData['GRAPH']
TOKENS = CHAIN.testData['TOKENS']
PRICE = CHAIN.testData['PRICE']
ARB_ROUTE = CHAIN.testData['ARB_ROUTE']


@pytest.fixture(scope='module')
def ChainSetup():
    CHAIN.buildGraph(EXCHANGES)
    return CHAIN


def equal(list1, list2):
    list_dif = [i for i in list1 + list2 if i not in list1 or i not in list2]
    return False if list_dif else True


def unique(items):
    seen = []
    for i in items:
        if i in seen:
            return False
        seen.append(i)
    return True


def test_BuildGraph(ChainSetup):
    assert ChainSetup.graph == GRAPH


def test_BuildExchanges(ChainSetup):
    pass


class TestArbRoute:

    def test_dive(self, ChainSetup):
        pass

    def test_DLS(self, ChainSetup):

        route = ChainSetup.DLS('AURORA', EXCHANGES)
        route2 = ChainSetup.DLS('WETH', )
        assert equal(route, ARB_ROUTE[:2])
        assert equal(route2, ARB_ROUTE[2:])

    def complete(self, chain, routes):
        for i in routes:
            if chain.simplyfy(i)[3] not in routes:
                return False
        return True

    # testing default as token
    def test_normalGetRoute(self, ChainSetup):
        route = ChainSetup.getArbRoute(tokens=TOKENS, save=False,
                                       exchanges='all', graph=False,
                                       screen=False)
        print(route)
        assert unique(route)
        assert self.complete(ChainSetup, route)

    @pytest.mark.parametrize('toks', [{}, ''])
    def test_invalidToken(self, ChainSetup, toks):
        with pytest.raises(ValueError):
            ChainSetup.getArbRoute(tokens=toks, save=False,
                                   exchanges='all', graph=False)

    @pytest.mark.parametrize('Exchanges,results',
                             [(['trisolaris'], ARB_ROUTE[::2]),
                              (['wannaswap'], ARB_ROUTE[1::2]),
                              (['auroraswap'], []),
                              (['trisolaris', 'wannaswap'], ARB_ROUTE)])
    def test_startExchanges(self, ChainSetup, Exchanges, results):
        route = ChainSetup.getArbRoute(tokens=TOKENS, save=False,
                                       exchanges=Exchanges, graph=False,
                                       screen=False)
        print(f'routes :- {route}')
        print(f'results :- {results}')
        assert equal(route, results)


prices1 = [
    {'AURORA': 21, 'WETH': 32},
    {'WETH': 55, 'NEAR': 41},
    {'NEAR': 70, 'AURORA': 40}
]
prices2 = [
    {'AURORA': 41, 'WETH': 32},
    {'WETH': 55, 'NEAR': 41},
    {'NEAR': 70, 'AURORA': 40}
]


class TestPollRoutes:

    @pytest.mark.parametrize('least,liquidity,prices', [
        (21, [21, 32, 41, 40], prices1),
        (32, [41, 32, 41, 40], prices2),
        ])
    def test_pollRoute(self, ChainSetup, least, liquidity, prices):
        simp = ChainSetup.simplyfy(ARB_ROUTE[0])
        rates = getRates(prices)
        reverse = liquidity[::-1]

        cap0 = least / rates[0][liquidity.index(least)] * ChainSetup.impact
        cap1 = least / rates[1][reverse.index(least)] * ChainSetup.impact
        ans = (
            [cap0, rates[0], ChainSetup.simulateSwap(simp[2], cap0, prices)],
            [cap1, rates[1], ChainSetup.simulateSwap(simp[3], cap1, prices[::-1])]  # noqa E501
        )
        res = ChainSetup.pollRoute(simp[2], prices=prices)
        print(f'answer {ans}')
        print(f'result {res}')
        assert ans == res

    def test_accurateReverse(self, ChainSetup):
        result = ChainSetup.pollRoute(ARB_ROUTE[0], prices=prices1)
        result2 = ChainSetup.pollRoute(ARB_ROUTE[1], prices=prices1[::-1])
        print(result)
        print(result2)
        assert result[1] == result2[0]
        assert result[0] == result2[1]

    def test_cumSum(self, ChainSetup):
        listItem = [2, 3, 1, 4]
        assert ChainSetup.cumSum(listItem) == [2, 6, 6, 24]

    def test_simplyfy(self, ChainSetup):
        ans = ['AURORA WETH trisolaris - WETH NEAR wannaswap - NEAR AURORA wannaswap',  # noqa E501
               'AURORA NEAR wannaswap - NEAR WETH wannaswap - WETH AURORA trisolaris',  # noqa E501
               ARB_ROUTE[0], ARB_ROUTE[1]]
        result = ChainSetup.simplyfy(ARB_ROUTE[0])
        assert result == ans


class TestgetPrice:

    @pytest.mark.skip(reason='incomplete')
    def test_extract(self, ChainSetup):
        pass

    @pytest.mark.skip(reason='incomplete')
    def test_getPrice(self, ChainSetup):
        assert True


def test_screenRoute(ChainSetup):
    routes = ARB_ROUTE
    screenedRoute = ARB_ROUTE[::2]

    result = ChainSetup.screenRoutes(routes=routes)
    assert equal(screenedRoute, result)


@pytest.mark.skip(reason='incomplete')
def test_priceLookup():
    pass
