import sys, os
sys.path.insert(1,
    os.path.join(os.path.split(os.path.dirname(__file__))[0],'scripts'))

import Blockchains
import pytest


exchanges = {
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

graph = {
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

tokens = ['AURORA','WETH']
price = {'WETH': 2.141651224104825, 'WBTC': 0.11160318}
arbRoute = [
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
def Aurorasetup():
    Aurora = Blockchains.Aurora()
    Aurora.buildGraph(exchanges) 
    return Aurora

def equal(list1,list2):
    list_dif = [i for i in list1 + list2 if i not in list1 or i not in list2]
    return False if list_dif else True

#@pytest.mark.noData
def test_BuildGraph(Aurorasetup):
    assert Aurorasetup.graph == graph

class TestArbRoute:
    #refactor the DLS tests to multiple ones
    def test_DLS(self,Aurorasetup):
        route = Aurorasetup.DLS('AURORA',exchanges)
        assert equal(route,arbRoute[:2])

    #testing default as token
    def test_normalGetRoute(self,Aurorasetup):
        route = Aurorasetup.getArbRoute(tokens = tokens, save = False,exchanges = 'all')
        assert equal(route,arbRoute)
    
    @pytest.mark.parametrize('toks',[{},''])
    def test_invalidToken(self,Aurorasetup,toks):
        with pytest.raises(ValueError):
            Aurorasetup.getArbRoute(tokens = toks, save = False,exchanges = 'all')

    @pytest.mark.parametrize('Exchanges,results',
        [(['trisolaris'],arbRoute[::2]),
        (['wannaswap'],arbRoute[1::2]),
        (['auroraswap'],[]),
        (['trisolaris','wannaswap'],arbRoute)])
    def test_startExchanges(self,Aurorasetup,Exchanges,results):
        route = Aurorasetup.getArbRoute(tokens = tokens, save = False,exchanges = Exchanges)
        assert equal(route,results)


class TestRate:

    def test_getRate(self,Aurorasetup):
        r1 = Aurorasetup.r1
        impact = Aurorasetup.impact
        rate = r1 * price['WETH'] / (1 + (impact * r1)) / price['WBTC']
        assert rate == Aurorasetup.getRate(price,'WETH','WBTC')

    @pytest.mark.parametrize('prices',[{'WETH': 2.141651224104825},{'WBTC': 0.11160318}])
    def test_invalidRate(self, Aurorasetup,prices):
        with pytest.raises(ValueError):
            Aurorasetup.getRate(prices,'WETH','WBTC')

prices = [
    {'AURORA' : 21,
    'WETH' : 32},
    {'WETH' : 55,
    'NEAR' : 41},
    {'NEAR' : 70,
    'AURORA' : 40}
]
class TestPollRoutes:
    
    def test_pollRoute(self,Aurorasetup):
        least = 21

        liquidity = [[32,41,40],[41,32,21]]
        rates1 = [Aurorasetup.getRate(prices[0],'WETH','AURORA')]
        rates2 = [Aurorasetup.getRate(prices[2],'NEAR','AURORA')]

        rates1.append(Aurorasetup.getRate(prices[1],'NEAR','WETH') * rates1[-1])
        rates2.append(Aurorasetup.getRate(prices[1],'WETH','NEAR') * rates2[-1])

        rates1.append(Aurorasetup.getRate(prices[2],'AURORA','NEAR') * rates1[-1])
        rates2.append(Aurorasetup.getRate(prices[0],'AURORA','WETH') * rates2[-1])

        ans = (Aurorasetup.getDetails(liquidity[0],least,rates1),
            Aurorasetup.getDetails(liquidity[1],least,rates2))
        res = Aurorasetup.pollRoute(arbRoute[0],prices = prices)
        assert ans == res

    def test_accurateReverse(self,Aurorasetup):
        result = Aurorasetup.pollRoute(arbRoute[0],prices = prices)
        result2 = Aurorasetup.pollRoute(arbRoute[1],prices = prices[::-1])
        print(result)
        print(result2)
        assert result[1] == result2[0]
        assert result[0] == result2[1]
    
    def test_pollingOnlyUnique(self,Aurorasetup):
        result = Aurorasetup.pollRoutes(arbRoute[:2], save = False)
        assert result[0]['requested'] == 1

    def test_pollingWarning(self,Aurorasetup):
        with pytest.warns(UserWarning):
            Aurorasetup.pollRoutes(arbRoute[:2], save = False)
    
    @pytest.mark.parametrize('least,result',[
        (21,[0.105,[0.5,0.5,0.5],-0.0525]),
        (40,[0.4,[0.5,0.5,0.5],-0.2]),
        (32,[0.32,[0.5,0.5,0.5],-0.16])])
    def test_getDetails(self,Aurorasetup,least,result):
        lists = [32,41,40]
        rates = [0.5,0.5,0.5]
        
        test = Aurorasetup.getDetails(lists,least,rates)
        assert test == result

    def test_cumSum(self,Aurorasetup):
        listItem = [2,3,1,4]
        assert Aurorasetup.cumSum(listItem) == [2,6,6,24]

        
    def test_simplyfy(self,Aurorasetup):
        ans = ['AURORA WETH trisolaris-WETH NEAR wannaswap-NEAR AURORA wannaswap',
            'AURORA NEAR wannaswap-NEAR WETH wannaswap-WETH AURORA trisolaris',
            arbRoute[0],arbRoute[1]]
        result = Aurorasetup.simplyfy(arbRoute[0])
        assert result == ans

class TestgetPrice:

    @pytest.mark.skip(reason = 'incomplete')
    def test_extract(self,Aurorasetup):
        pass

    @pytest.mark.skip(reason = 'incomplete')
    def test_getPrice(self,Aurorasetup):
        assert True


def test_screenRoute(Aurorasetup):
    routes = arbRoute
    screenedRoute = arbRoute[::2]

    result = Aurorasetup.screenRoutes(routes = routes,save = False)
    assert equal(screenedRoute,result)

class TestExceution:

    @pytest.mark.skip(reason = 'incomplete')
    def test_execution(self,):
        assert True