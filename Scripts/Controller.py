'''The controller class that prepares and executes arbs'''
import scripts.Config as Cfg
import scripts.Errors as errors
from scripts.utills import sortTokens, isTestnet
import scripts.Models as models

import os
from eth_abi import encode_abi
from web3 import Web3
import attr
import logging
from typing import Type

log = logging.getLogger()


@attr.s
class Controller():

    def __attrs_post_init__(self) -> None:
        self.simplyfied = self.simplyfy(self.swaps)

    def __init__(self, blockchain: Type[models.BaseBlockchain]) -> None:
        self.blockchainMap = Cfg.ControllerBlockchains
        if str(blockchain) in self.blockchainMap:
            self.blockchain = blockchain
        else:
            raise errors.InvalidBlockchainObject(
                f'Invalid Blockchain Object {blockchain}')

        self.contractAbi = Cfg.contractAbi
        self.contractAddress = self.blockchain.arbAddress
        self.routerAbi = Cfg.routerAbi
        self.swapFuncSig = '0x38ed1739'
        # 'swapExactTokensForTokens(uint256,uint256,address[],address,uint256)'
        self.approveFuncSig = '0x095ea7b3'
        # 'approve(address,uint256)'
        self.optimalAmount = 1.009027027
        self.web3 = Web3(Web3.HTTPProvider(self.blockchain.url,
                                           request_kwargs={'timeout': 300}))
        self.pv = os.environ.get('BEACON')

    def getContract(self, address='', abi=''):
        if not address:
            address = self.contractAddress
        if not abi:
            abi = self.contractAbi
        return self.web3.eth.contract(address=address, abi=abi)

    def getAccount(self):
        if isTestnet(self.blockchain):
            return self.web3.eth.accounts[0]
        else:
            return self.web3.eth.account.from_key(self.pv)

    '''def getRoutes(self, pollResult = True, arbRoute = False):
        history = set()

        if arbRoute:
            self.blockchain.pollRoutes()
            pollResult = True

        if pollResult:
            try:
                with open(self.blockchain.pollPath, 'r') as PP:
                    pollPath = json.load(PP)
            except FileNotFoundError:
                warnings.warn('Poll result file not found')
            else:
                for item in pollPath['Data']:
                    route = self.blockchain.assemble(item['route'])
                    routes = self.blockchain.simplyfy(route)
                    history.add(routes[0])
                    history.add(routes[1])
                    if item['EP'] > 0:
                        yield {'route' : routes[2],'simplified' : routes[0],'EP' : item['EP'],'capital' : item['capital']}  # noqa: E501

    '''
    '''def check(self, route):
        return self.blockchain.pollRoute(route)
'''
    def getProspect(self, Routes):
        for item in Routes:
            simplyfied = self.blockchain.simplyfy(item['route'])
            if 'EP' in item and item['EP']/item['capital'] >= self.optimalAmount:  # noqa: E501
                item['EP'] *= 1e18
                item['capital'] *= 1e18
                item['simplified'] = simplyfied[0]
                item['route'] = simplyfied[2]
                yield item
            elif 'EP' not in item and str(self.blockchain)[-7:] != 'Testnet':
                result = self.check(item['route'])

                if result[0][2] / result[0][0] >= self.optimalAmount:
                    item['EP'] = result[0][2] * 1e18
                    item['capital'] = result[0][0] * 1e18
                    item['simplified'] = simplyfied[0]
                    yield item
                elif result[1][2] / result[1][0] >= self.optimalAmount:
                    item['EP'] = result[1][2] * 1e18
                    item['capital'] = result[1][0] * 1e18
                    item['simplified'] = simplyfied[1]
                    item['route'] = simplyfied[3]
                    yield item

    def getAmountsOut(self, routerAddress, amount, addresses):
        Router = self.getContract(routerAddress, self.routerAbi)
        amounts = Router.functions.getAmountsOut(amount, addresses).call()
        return amounts[-1]

    def simulateSwap(self, route, routers, cap, tokens):
        current = int(cap)
        for index, i in enumerate(route):
            fro = tokens[i['from']]
            to = tokens[i['to']]
            nexxt = self.getAmountsOut(routers[index], current, [fro, to])
            current = nexxt
        return current

    def getValues(self, item, options):
        '''
        options contents

        * all items are optional

        tokens :- dict
        pair :- address
        factory :- address
        router :- list
        '''
        values = {}

        if 'tokens' in options:
            values['tokens'] = options['tokens']
        else:
            values['tokens'] = self.blockchain.tokens

        values['names'] = names = (
            item['route'][0]['from'], item['route'][0]['to'])

        if 'routers' in options:
            assert len(item['route']) == len(options['routers'])
            values['routers'] = options['routers']
        else:
            routers = []
            for i in item['route']:
                routers.append(self.blockchain.exchanges[i['via']]['router'])
            values['routers'] = routers

        if 'pair' in options:
            values['pair'] = options['pair']
        else:
            values['pair'] = self.blockchain.exchanges[
                item['route'][0]['via']]['pairs'][frozenset((names[0], names[1]))]  # noqa: E501

        if 'factory' in options:
            values['factory'] = options['factory']

        if 'fee' in options:
            values['fee'] = options['fee']
        else:
            values['fee'] = self.blockchain.exchanges[
                item['route'][0]['via']]['fee']

        return values

    def prepPayload(self, item, options={}, simulate=False):

        val = self.getValues(item=item, options=options)

        tokens, amount = val['tokens'], int(item['capital'])
        addresses, data = [], []

        fee = val['fee']

        rem = item['route'][1:]
        end = len(rem) - 1

        for index, i in enumerate(rem):
            router = val['routers'][index + 1]

            # to populate the addresses list
            if index == 0 or rem[index - 1]['via'] != i['via']:
                addr = [tokens[i['from']], tokens[i['to']]]
                addresses.append(router)
                print(f'addresses snapshot, index {index} :- {addresses}')
            else:
                addr.append(tokens[i['to']])

            # to populate the data list
            if index == end or rem[index + 1]['via'] != i['via']:
                defs, args = ['address[]'], [addr]
                print(f'addr snapshot, index {index} :- {addr}')
                data.append(encode_abi(defs, args))

        defs = ['address[]', 'bytes[]', 'address', 'uint256', 'uint256']
        args = [addresses, data, val['pair'], amount, fee]

        # print(args)
        DATA = Web3.toHex(encode_abi(defs, args))

        names = val['names']
        token0 = sortTokens(tokens[names[0]], tokens[names[1]])[0]

        if 'out' not in options:
            start = self.getAmountsOut(
                    val['routers'][0], amount,
                    [tokens[val['names'][0]], tokens[val['names'][1]]])
        else:
            start = int(options['out'] * amount)

        AMOUNT0 = start if tokens[names[0]] == token0 else 0
        AMOUNT1 = 0 if tokens[names[0]] == token0 else start

        # print(f'final payload :- {AMOUNT0,AMOUNT1,tokens[names[0]],DATA}')

        return {
            'profitable': None,
            'data': [AMOUNT0, AMOUNT1, tokens[names[0]], DATA]}

    def execute(self, payload):
        contract = self.getContract()
        account = self.getAccount()

        if isTestnet(self.blockchain):
            tranx = contract.functions.start(
                *payload).transact({'from': account})
        else:
            rawTx = contract.functions.start(*payload).buildTransaction(
                {'from': account,
                 'nonce': self.web3.eth.get_transaction_count(account.address)}
            )
            txCreate = self.web3.eth.account.sign_transaction(rawTx, self.pv)
            tranx = self.web3.eth.send_raw_transaction(txCreate.rawTransaction)

        txReceipt = self.web3.eth.wait_for_transaction_receipt(tranx)
        print(f'tx succesful with hash: {txReceipt.transactionHash.hex()}')

    def arb(self, routes=[], amount=10,  keyargs=[]):

        # keyargs is a list of dictionaries
        if not routes:
            routes = self.getRoutes()
        lenght = len(routes)

        if keyargs:
            assert len(keyargs) == lenght

        Prospects = self.getProspect(routes)

        try:
            for i in range(amount):
                print(f'arbing {i + 1} of {lenght} routes')
                prospect = next(Prospects)

                if not keyargs:
                    payload = self.prepPayload(prospect, simulate=True)
                else:
                    payload = self.prepPayload(prospect,
                                               keyargs[i], simulate=True)

                if payload['profitable']:
                    self.execute(payload['data'])

        except StopIteration:
            print('route items exhausted!')

    def scanPair(self):
        # get reserves and compare against balances
        pass

    def getSkimProspect(self):
        # scan and yields profitable pairs
        pass

    def storeSkimProspect(self):
        # save the profitable pairs in a json file
        pass

    def skim(self, skims=[], source=''):
        # Execute the profitable pairs
        pass
