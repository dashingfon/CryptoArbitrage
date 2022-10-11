import scripts.Blockchains as Blc

import pytest
from brownie import interface


Data_Available = 0
ChaiN = 'Binance'


@pytest.fixture(scope='module')
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
        return (address2, address1)
    elif first < second:
        return (address1, address2)
    else:
        raise ValueError('Addresses are the same')


def prepChain():
    Chain = getChain()
    result = [[], [], [], [], []]
    for exchange, item in Chain.exchanges.items():
        for key, value in item['pairs'].items():
            result[0].append(list(key))
            result[1].append(value)
            result[2].append(exchange)
        result[3].append(item['router'])
        result[4].append(item['factory'])
    return result


RESULT = prepChain()


def Contract(idd, address):
    if idd == 'Factory':
        return interface.IFactory(address)
    elif idd == 'Router':
        return interface.IRouter(address)
    elif idd == 'Pair':
        return interface.IPair(address)
    else:
        raise ValueError


def test_router_factories(Chain):
    routerLen = len(Chain.exchanges)
    page = 1
    for exchange, item in Chain.exchanges.items():
        print(f'\rPage {page} of {routerLen}')
        router = item['router']
        factory = item['factory']
        contract = Contract('Router', router)
        got = contract.factory().lower()
        if got != factory.lower():
            print(f'Exchange {exchange} router factory incorrect')
            print(f'Got :- {got}')
            print(f'Expected :- {factory.lower()}')
            print('')
        page += 1


def test_pairs_factories(Chain):
    excLen = len(Chain.exchanges)
    page = 1
    for exchange, item in Chain.exchanges.items():
        factory = Chain.exchanges[exchange]['factory']
        pair = 1
        for tokens, address in item['pairs'].items():
            print(f'\rExchange {page} of {excLen}, Pair {pair}')
            contract = Contract('Pair', address)
            got = contract.factory().lower()
            if got != factory.lower():
                print(f'Exchange {exchange}, Pair {tokens} factory incorrect')
                print(f'Got :- {got}')
                print(f'Expected :- {factory.lower()}')
                print('')
            pair += 1
        page += 1


def test_factories_pairs(Chain):
    toks = Chain.tokens
    excLen = len(Chain.exchanges)
    page = 1
    for exchange, item in Chain.exchanges.items():
        factory = Chain.exchanges[exchange]['factory']
        pair = 1
        for tokens, address in item['pairs'].items():
            print(f'\rExchange {page} of {excLen}, Pair {pair}')
            tokens = list(tokens)
            contract = Contract('Factory', factory)
            got = contract.getPair(toks[tokens[0]], toks[tokens[1]]).lower()
            if got != address.lower():
                print(f'Exchange {exchange}, Pair {tokens} incorrect')
                print(f'Got :- {got}')
                print(f'Expected :- {address.lower()}')
                print(f'Token addresses :- {(toks[tokens[0]],toks[tokens[1]])}')  # noqa
                print('')
            pair += 1
        page += 1


class TestExchanges():

    @pytest.mark.parametrize('tokens,pairAddress,exchanges',
                             [tuple(RESULT[0]), tuple(RESULT[1]), tuple(RESULT[2])])
    def test_exchangesPairs(self, tokens, pairAddress, Chain, exchanges):
        toks = getTokens()
        tokenSorted = sortTokens(toks[tokens[0]], toks[tokens[1]])
        token0 = Chain.tokens[tokenSorted[0]]
        token1 = Chain.tokens[tokenSorted[1]]
        factory = Chain.exchanges[exchanges]['factory']

        contract = FACTORY_INTERFACE(factory)
        assert contract.getPair(token0, token1).lower() == pairAddress.lower()

    @pytest.mark.parametrize('pairAddress,exchanges',
                             [tuple(RESULT[1]), tuple(RESULT[2])])
    def testFactories(self, pairAddress, Chain, exchanges):
        factory = Chain.exchanges[exchanges]['factory']

        contract = PAIR_INTERFACE(pairAddress)
        assert contract.factory().lower() == factory.lower()

    '''@pytest.mark.parametrize('router,factory',
        [tuple(RESULT[3]),tuple(RESULT[4])])
    def testRouters(self,factory,router):
        contract = PAIR_INTERFACE(router)
        assert contract.factory().lower() == factory.lower()'''
