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


FACTORY_INTERFACE = interface.IFactory
PAIR_INTERFACE = interface.IPair


def sortTokens(address1, address2):
    first = str.encode(address1).hex()
    second = str.encode(address2).hex()

    if first > second:
        return (address2,address1)
    elif first < second:
        return (address1,address2)
    else:
        raise ValueError('Addresses are the same')


def prepChain(Chain):
    result = [[],[],[]]
    for exchange, item in Chain.exchanges.values():
        for key, value in item['pairs'].items():
            result[0].append(list(key))
            result[1].append(value)
            result[2].append(exchange)
    return result

RESULT = prepChain()

class TestExchanges():
    
    @pytest.mark.parametrize('tokens,pairAddress,exchanges',
        [tuple(RESULT[0]),tuple(RESULT[1]),tuple(RESULT[2])])
    def test_exchangesPairs(self,tokens,pairAddress,Chain,exchanges):
        tokenSorted = sortTokens(tokens[0],tokens[1])
        token0 = Chain.tokens[tokenSorted[0]]
        token1 = Chain.tokens[tokenSorted[1]]
        factory = Chain.exchanges[exchanges]['factory']

        contract = FACTORY_INTERFACE(factory)
        assert contract.getPair(token0,token1) == pairAddress
    
    @pytest.mark.parametrize('pairAddress,exchanges',
        [tuple(RESULT[1]),tuple(RESULT[2])])
    def testFactories(self,pairAddress,Chain,exchanges):
        factory = Chain.exchanges[exchanges]['factory']

        contract = PAIR_INTERFACE(pairAddress)
        assert contract.factory() == factory

