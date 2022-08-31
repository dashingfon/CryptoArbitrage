import sys, os

sys.path.insert(1,
    os.path.join(os.path.split(os.path.dirname(__file__))[0],'scripts'))

import Blockchains as Blc
import pytest
from brownie import interface


Data_Available = 0

ChaiN = 'Binance'
@pytest.fixture(scope = 'module')
def Chain():
    if ChaiN == 'Aurora':
        return Blc.Aurora()
    elif ChaiN == 'Binance':
        return Blc.BSC()
    else:
        raise Exception('Incorrect BlockChain Object!')

def getChain():
    if ChaiN == 'Aurora':
        return Blc.Aurora()
    elif ChaiN == 'Binance':
        return Blc.BSC()
    else:
        raise Exception('Incorrect BlockChain Object!')

def getTokens():
    chain = getChain()
    return chain.tokens

FACTORY_INTERFACE = interface.IFactory
PAIR_INTERFACE = interface.IPair
ROUTER_INTERFACE = interface.IRouter


def sortTokens(address1, address2):
    first = str.encode(address1).hex()
    second = str.encode(address2).hex()

    if first > second:
        return (address2,address1)
    elif first < second:
        return (address1,address2)
    else:
        raise ValueError('Addresses are the same')


def prepChain():
    Chain = getChain()
    result = [[],[],[],[],[]]
    for exchange, item in Chain.exchanges.items():
        for key, value in item['pairs'].items():
            result[0].append(list(key))
            result[1].append(value)
            result[2].append(exchange)
        result[3].append(item['router'])
        result[4].append(item['factory'])
    return result

RESULT = prepChain()

class TestExchanges():
    
    @pytest.mark.parametrize('tokens,pairAddress,exchanges',
        [tuple(RESULT[0]),tuple(RESULT[1]),tuple(RESULT[2])])
    def test_exchangesPairs(self,tokens,pairAddress,Chain,exchanges):
        toks = getTokens()
        tokenSorted = sortTokens(toks[tokens[0]],toks[tokens[1]])
        token0 = Chain.tokens[tokenSorted[0]]
        token1 = Chain.tokens[tokenSorted[1]]
        factory = Chain.exchanges[exchanges]['factory']

        contract = FACTORY_INTERFACE(factory)
        assert contract.getPair(token0,token1).lower() == pairAddress.lower()
    
    @pytest.mark.parametrize('pairAddress,exchanges',
        [tuple(RESULT[1]),tuple(RESULT[2])])
    def testFactories(self,pairAddress,Chain,exchanges):
        factory = Chain.exchanges[exchanges]['factory']

        contract = PAIR_INTERFACE(pairAddress)
        assert contract.factory().lower() == factory.lower()

    '''@pytest.mark.parametrize('router,factory',
        [tuple(RESULT[3]),tuple(RESULT[4])])
    def testRouters(self,factory,router):
        contract = PAIR_INTERFACE(router)
        assert contract.factory().lower() == factory.lower()'''