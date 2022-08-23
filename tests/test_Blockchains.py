import sys, os
sys.path.insert(1,
    os.path.join(os.path.split(os.path.dirname(__file__))[0],'scripts'))

import Blockchains
import pytest

Data_Available = 0
Chain = 'Aurora'
def getChain():
    if Chain == 'Aurora':
        return Blockchains.Aurora()
    elif Chain == 'Kovan' :
        return Blockchains.Kovan()
    else:
        raise ValueError('Invalid Chain Argument')

CHAIN = getChain()

EXCHANGES = CHAIN.testData['EXCHANGES']
GRAPH = CHAIN.testData['GRAPH']
TOKENS = CHAIN.testData['TOKENS']
PRICE = CHAIN.testData['PRICE']
ARB_ROUTE = CHAIN.testData['ARB_ROUTE']

@pytest.fixture(scope = 'module')
def ChainSetup(): 
    CHAIN.buildGraph(EXCHANGES)
    return CHAIN


def equal(list1,list2):
    list_dif = [i for i in list1 + list2 if i not in list1 or i not in list2]
    return False if list_dif else True


def test_BuildGraph(ChainSetup):
    assert ChainSetup.graph == GRAPH

class TestArbRoute:

    def test_DLS(self,ChainSetup):
        route = ChainSetup.DLS('AURORA',EXCHANGES)
        route2 = ChainSetup.DLS('WETH',EXCHANGES)
        assert equal(route,ARB_ROUTE[:2])
        assert equal(route2,ARB_ROUTE[2:])

    #testing default as token
    def test_normalGetRoute(self,ChainSetup):
        route = ChainSetup.getArbRoute(tokens = TOKENS, save = False,exchanges = 'all',graph = False)
        assert equal(route,ARB_ROUTE)
    
    @pytest.mark.parametrize('toks',[{},''])
    def test_invalidToken(self,ChainSetup,toks):
        with pytest.raises(ValueError):
            ChainSetup.getArbRoute(tokens = toks, save = False,exchanges = 'all',graph = False)

    @pytest.mark.parametrize('Exchanges,results',
        [(['trisolaris'],ARB_ROUTE[::2]),
        (['wannaswap'],ARB_ROUTE[1::2]),
        (['auroraswap'],[]),
        (['trisolaris','wannaswap'],ARB_ROUTE)])
    def test_startExchanges(self,ChainSetup,Exchanges,results):
        route = ChainSetup.getArbRoute(tokens = TOKENS, save = False,exchanges = Exchanges,graph = False)
        print(route)
        assert equal(route,results)

class TestRate:

    def test_getRate(self,ChainSetup):
        r1 = ChainSetup.r1
        impact = ChainSetup.impact
        rate = r1 * PRICE['WETH'] / (1 + (impact * r1)) / PRICE['WBTC']
        assert rate == ChainSetup.getRate(PRICE,'WETH','WBTC')

    @pytest.mark.parametrize('prices',[{'WETH': 2.141651224104825},{'WBTC': 0.11160318}])
    def test_invalidRate(self, ChainSetup,prices):
        with pytest.raises(ValueError):
            ChainSetup.getRate(prices,'WETH','WBTC')

prices = [
    {'AURORA' : 21,
    'WETH' : 32},
    {'WETH' : 55,
    'NEAR' : 41},
    {'NEAR' : 70,
    'AURORA' : 40}
]
rates1 = [1,ChainSetup.getRate(prices[0],'WETH','AURORA')]
rates2 = [1,ChainSetup.getRate(prices[2],'NEAR','AURORA')]

rates1.append(ChainSetup.getRate(prices[1],'NEAR','WETH') * rates1[-1])
rates2.append(ChainSetup.getRate(prices[1],'WETH','NEAR') * rates2[-1])

rates1.append(ChainSetup.getRate(prices[2],'AURORA','NEAR') * rates1[-1])
rates2.append(ChainSetup.getRate(prices[0],'AURORA','WETH') * rates2[-1])

class TestPollRoutes:
    
    @pytest.parametrize('least,liquidity,result',[
        (21,[21,32,41,40]),
        (32,[41,32,41,40]),
        ])
    def test_pollRoute(self,ChainSetup,least,liquidity,result):

        reverse = liquidity[::-1]
    
        ans = (
            [],
            []
        )
        res = ChainSetup.pollRoute(ARB_ROUTE[0],prices = prices)
        assert ans == res

    def test_accurateReverse(self,ChainSetup):
        result = ChainSetup.pollRoute(ARB_ROUTE[0],prices = prices)
        result2 = ChainSetup.pollRoute(ARB_ROUTE[1],prices = prices[::-1])
        print(result)
        print(result2)
        assert result[1] == result2[0]
        assert result[0] == result2[1]
        
    @pytest.mark.xfail(not Data_Available,reason = 'no data connection')
    def test_pollingOnlyUnique(self,ChainSetup):
        result = ChainSetup.pollRoutes(ARB_ROUTE[:2], save = False, screen = False)
        assert result[0]['requested'] == 1

    @pytest.mark.xfail(not Data_Available, reason = 'no data connection')
    def test_pollingWarning(self,ChainSetup):
        with pytest.warns(UserWarning):
            ChainSetup.pollRoutes(ARB_ROUTE[:2], save = False, screen = False)
    

    def test_cumSum(self,ChainSetup):
        listItem = [2,3,1,4]
        assert ChainSetup.cumSum(listItem) == [2,6,6,24]

        
    def test_simplyfy(self,ChainSetup):
        ans = ['AURORA WETH trisolaris - WETH NEAR wannaswap - NEAR AURORA wannaswap',
            'AURORA NEAR wannaswap - NEAR WETH wannaswap - WETH AURORA trisolaris',
            ARB_ROUTE[0],ARB_ROUTE[1]]
        result = ChainSetup.simplyfy(ARB_ROUTE[0])
        assert result == ans

class TestgetPrice:

    @pytest.mark.skip(reason = 'incomplete')
    def test_extract(self,ChainSetup):
        pass

    @pytest.mark.skip(reason = 'incomplete')
    def test_getPrice(self,ChainSetup):
        assert True


def test_screenRoute(ChainSetup):
    routes = ARB_ROUTE
    screenedRoute = ARB_ROUTE[::2]

    result = ChainSetup.screenRoutes(routes = routes)
    assert equal(screenedRoute,result)


@pytest.mark.skip(reason = 'incomplete')
def test_priceLookup():
    pass

