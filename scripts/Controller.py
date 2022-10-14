'''The controller class that prepares and executes arbs'''

from scripts import CONFIG_PATH
import scripts.Models as models
import scripts.Errors as errors
from scripts.Utills import sortTokens, readJson

import os
import attr
import logging
from web3 import Web3
from typing import Any
from eth_abi import encode_abi
from dotenv import load_dotenv


load_dotenv()
Config: dict = readJson(CONFIG_PATH)


@attr.s
class Controller():

    def __init__(self, blockchain: Any,
                 testing: bool = False) -> None:

        self.verifyChain(blockchain)
        self.contractAbi: list = Cfg.contractAbi
        self.routerAbi: list = Cfg.routerAbi
        self.swapFuncSig: str = '0x38ed1739'
        # 'swapExactTokensForTokens(uint256,uint256,address[],address,uint256)'
        self.approveFuncSig: str = '0x095ea7b3'
        # 'approve(address,uint256)'
        self.optimalAmount: float = 1.009027027
        self.web3: Web3 = Web3(Web3.HTTPProvider(self.blockchain.url,
                                           request_kwargs={'timeout': 300}))  # noqa E128
        self.pv: str | None = os.environ.get('BEACON')
        self.testing = testing

    def verifyChain(self, blockchain: Any) -> None:
        if issubclass(type(blockchain), models.BaseBlockchain):
            self.blockchain: Any = blockchain
        else:
            raise errors.InvalidBlockchainObject(
                f'Invalid Blockchain Object {blockchain}')

    def getContract(self, address: str = '',
                    abi: list = []) -> Any:
        if not address and not self.blockchain.arbAddress:
            raise errors.NoBlockchainContract(
                f'{self.blockchain} has no contract address'
            )
        elif not address:
            address = self.blockchain.arbAddress

        if not abi:
            abi = self.contractAbi
        return self.web3.eth.contract(address=address, abi=abi)

    def getAccount(self) -> Any:
        if self.testing:
            return self.web3.eth.accounts[0]
        elif not self.pv:
            raise errors.PrivateKeyNotSet('no private key set')
        else:
            return self.web3.eth.account.from_key(self.pv)

    def getProspect(self, Routes):

        pass

    def getAmountsOut(self, routerAddress: str, amount: int,
                      addresses: list[str]) -> int:
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

    def getValues(self, item: dict, options: dict) -> dict:
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

    def prepPayload(self, item, options={}, simulate=False, **others):

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

        if self.testing(self.blockchain):
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
        logging.info(f'tx succesful with hash: {txReceipt.transactionHash.hex()}')  # noqa

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
