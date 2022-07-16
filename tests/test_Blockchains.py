import sys, os
sys.path.insert(1,
    os.path.join(os.path.split(os.path.dirname(__file__))[0],'scripts'))

import Blockchains
import pytest

DATA_AVAILABLE = 0

EXCHANGES = {
    'trisolaris' : {
        'pairs' : {
        frozenset(('AURORA', 'WETH')) : '0x5eeC60F348cB1D661E4A5122CF4638c7DB7A886e',
        frozenset(('NEAR', 'USDT')) : '0x03B666f3488a7992b2385B12dF7f35156d7b29cD',}},
    'auroraswap' : {
        'pairs' : {
        frozenset(('USDT', 'USDC')) : '0xec538fafafcbb625c394c35b11252cef732368cd',
        frozenset(('USDC', 'NEAR')) : '0x480a68ba97d70495e80e11e05d59f6c659749f27',}},
    'wannaswap' : {
        'pairs' : {
        frozenset(('AURORA', 'NEAR')) : '0x7e9ea10e5984a09d19d05f31ca3cb65bb7df359d',
        frozenset(('NEAR', 'WETH')) : '0x256d03607eee0156b8a2ab84da1d5b283219fe97',
        frozenset(('USDC', 'NEAR')) : '0xbf560771b6002a58477efbcdd6774a5a1947587b',}
        }}

GRAPH = {
    'AURORA' : [
        {'to' : 'WETH','via' : 'trisolaris',},
        {'to' : 'NEAR','via' : 'wannaswap',},],
    'WETH' : [
        {'to' : 'AURORA','via' : 'trisolaris',},
        {'to' : 'NEAR','via' : 'wannaswap',},],
    'NEAR' : [
        {'to' : 'USDT','via' : 'trisolaris',},
        {'to' : 'USDC','via' : 'auroraswap',},
        {'to' : 'AURORA','via' : 'wannaswap',},
        {'to' : 'WETH','via' : 'wannaswap',},
        {'to' : 'USDC','via' : 'wannaswap',},],
    'USDC' : [
        {'to' : 'USDT','via' : 'auroraswap',},
        {'to' : 'NEAR','via' : 'auroraswap',},
        {'to' : 'NEAR','via' : 'wannaswap',},],
    'USDT': [
        {'to' : 'NEAR','via' : 'trisolaris',},
        {'to' : 'USDC','via' : 'auroraswap',},],
}

TOKENS = ['AURORA','WETH']
PRICE = {'WETH': 2.141651224104825, 'WBTC': 0.11160318}
ARB_ROUTE = [
    [
        {
        'from' : 'AURORA',
        'to' : 'WETH',
        'via' : 'trisolaris'},
        {
        'from' : 'WETH',
        'to' : 'NEAR',
        'via' : 'wannaswap'},
        {
        'from' : 'NEAR',
        'to' : 'AURORA',
        'via' : 'wannaswap'},
    ],
    [
        {
        'from' : 'AURORA',
        'to' : 'NEAR',
        'via' : 'wannaswap'},
        {
        'from' : 'NEAR',
        'to' : 'WETH',
        'via' : 'wannaswap'},
        {
        'from' : 'WETH',
        'to' : 'AURORA',
        'via' : 'trisolaris'},
    ],
    [
        {
        'from' : 'WETH',
        'to' : 'AURORA',
        'via' : 'trisolaris'},
        {
        'from' : 'AURORA',
        'to' : 'NEAR',
        'via' : 'wannaswap'},
        {
        'from' : 'NEAR',
        'to' : 'WETH',
        'via' : 'wannaswap'},
    ],
    [
        {
        'from' : 'WETH',
        'to' : 'NEAR',
        'via' : 'wannaswap'},
        {
        'from' : 'NEAR',
        'to' : 'AURORA',
        'via' : 'wannaswap'},
        {
        'from' : 'AURORA',
        'to' : 'WETH',
        'via' : 'trisolaris'},
    ],
    ]

@pytest.fixture(scope = 'module')
def ChainSetup():
    Aurora = Blockchains.Aurora()
    Aurora.buildGraph(EXCHANGES) 
    return Aurora

def equal(list1,list2):
    list_dif = [i for i in list1 + list2 if i not in list1 or i not in list2]
    return False if list_dif else True

#@pytest.mark.noData
def test_BuildGraph(ChainSetup):
    assert ChainSetup.graph == GRAPH

class TestArbRoute:
    #refactor the DLS tests to multiple ones
    def test_DLS(self,ChainSetup):
        route = ChainSetup.DLS('AURORA',EXCHANGES)
        assert equal(route,ARB_ROUTE[:2])

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
class TestPollRoutes:
    
    def test_pollRoute(self,ChainSetup):
        least = 21

        liquidity = [[32,41,40],[41,32,21]]
        rates1 = [ChainSetup.getRate(prices[0],'WETH','AURORA')]
        rates2 = [ChainSetup.getRate(prices[2],'NEAR','AURORA')]

        rates1.append(ChainSetup.getRate(prices[1],'NEAR','WETH') * rates1[-1])
        rates2.append(ChainSetup.getRate(prices[1],'WETH','NEAR') * rates2[-1])

        rates1.append(ChainSetup.getRate(prices[2],'AURORA','NEAR') * rates1[-1])
        rates2.append(ChainSetup.getRate(prices[0],'AURORA','WETH') * rates2[-1])

        ans = (ChainSetup.getDetails(liquidity[0],least,rates1),
            ChainSetup.getDetails(liquidity[1],least,rates2))
        res = ChainSetup.pollRoute(ARB_ROUTE[0],prices = prices)
        assert ans == res

    def test_accurateReverse(self,ChainSetup):
        result = ChainSetup.pollRoute(ARB_ROUTE[0],prices = prices)
        result2 = ChainSetup.pollRoute(ARB_ROUTE[1],prices = prices[::-1])
        print(result)
        print(result2)
        assert result[1] == result2[0]
        assert result[0] == result2[1]
        
    @pytest.mark.xfail(not DATA_AVAILABLE,reason = 'no data connection')
    def test_pollingOnlyUnique(self,ChainSetup):
        result = ChainSetup.pollRoutes(ARB_ROUTE[:2], save = False)
        assert result[0]['requested'] == 1

    @pytest.mark.xfail(not DATA_AVAILABLE, reason = 'no data connection')
    def test_pollingWarning(self,ChainSetup):
        with pytest.warns(UserWarning):
            ChainSetup.pollRoutes(ARB_ROUTE[:2], save = False)
    
    @pytest.mark.parametrize('least,result',[
        (21,[0.105,[0.5,0.5,0.5],-0.0525]),
        (40,[0.4,[0.5,0.5,0.5],-0.2]),
        (32,[0.32,[0.5,0.5,0.5],-0.16])])
    def test_getDetails(self,ChainSetup,least,result):
        lists = [32,41,40]
        rates = [0.5,0.5,0.5]
        
        test = ChainSetup.getDetails(lists,least,rates)
        assert test == result

    def test_cumSum(self,ChainSetup):
        listItem = [2,3,1,4]
        assert ChainSetup.cumSum(listItem) == [2,6,6,24]

        
    def test_simplyfy(self,ChainSetup):
        ans = ['AURORA WETH trisolaris-WETH NEAR wannaswap-NEAR AURORA wannaswap',
            'AURORA NEAR wannaswap-NEAR WETH wannaswap-WETH AURORA trisolaris',
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

    result = ChainSetup.screenRoutes(routes = routes,save = False)
    assert equal(screenedRoute,result)

class TestExceution:

    @pytest.mark.skip(reason = 'incomplete')
    def test_execution(self,):
        assert True