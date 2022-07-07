import sys, os 
sys.path.insert(1,
    os.path.join(os.path.split(os.path.dirname(__file__))[0],'scripts'))

import Blockchains
import pytest


exchanges = {
    'trisolaris' : {
        frozenset(('AURORA', 'WETH')) : '0x5eeC60F348cB1D661E4A5122CF4638c7DB7A886e',
        frozenset(('NEAR', 'USDT')) : '0x03B666f3488a7992b2385B12dF7f35156d7b29cD',},
    'auroraswap' : {
        frozenset(('USDT', 'USDC')) : '0xec538fafafcbb625c394c35b11252cef732368cd',
        frozenset(('USDC', 'NEAR')) : '0x480a68ba97d70495e80e11e05d59f6c659749f27',},
    'wannaswap' : {
        frozenset(('AURORA', 'NEAR')) : '0x7e9ea10e5984a09d19d05f31ca3cb65bb7df359d',
        frozenset(('NEAR', 'WETH')) : '0x256d03607eee0156b8a2ab84da1d5b283219fe97',
        frozenset(('USDC', 'NEAR')) : '0xbf560771b6002a58477efbcdd6774a5a1947587b',}}

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

class TestPollRoute:

    @pytest.mark.skip(reason = 'incomplete')
    def test_pollRoute():
        assert True

class TestgetPrice:

    @pytest.mark.skip(reason = 'incomplete')
    def test_getPrice():
        assert True

class TestExceution:

    @pytest.mark.skip(reason = 'incomplete')
    def test_execution(self,):
        assert True