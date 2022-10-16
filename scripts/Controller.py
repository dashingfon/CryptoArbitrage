'''The controller class that prepares and executes arbs'''

from scripts import CONFIG_PATH
import scripts.Errors as errors
from scripts.Models import (
    BaseBlockchain,
    Route
)
from scripts.Utills import sortTokens, readJson

import os
import attr
import logging
from web3 import Web3
from typing import (
    Any,
    Optional,
    Type
    )
from eth_abi import encode_abi
from dotenv import load_dotenv


load_dotenv()
Config: dict = readJson(CONFIG_PATH)


@attr.s
class Controller():
    blockchain: Type[BaseBlockchain] = attr.ib()

    @blockchain.validator
    def verifyChain(self, attribute, value) -> None:
        if not issubclass(type(value), BaseBlockchain):
            raise errors.InvalidBlockchainObject(
                f'Invalid Blockchain Object {value}')

        if not value.url:
            raise errors.EmptyBlockchainUrl(
                'Blockchain Objects url is empty')

    testing: bool = attr.ib()
    pv: Optional[str] = attr.ib(default=os.environ.get('BEACON'))
    contractAbi: list = attr.ib(default=Config['ABIs']["ContractAbi"])
    routerAbi: list = attr.ib(default=Config['ABIs']["RouterAbi"])
    optimalAmount: float = attr.ib(default=1.009027027)
    web3: Web3 = attr.ib(default=(Web3(Web3.HTTPProvider(
                  blockchain.url, request_kwargs={'timeout': 300}))))

    @property
    def swapFuncSig(self) -> str:
        return '0x38ed1739'  # swapExactTokenForTokens()

    @property
    def approveFuncSig(self) -> str:
        return '0x095ea7b3'  # approve()

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

    def prepPayload(self, item, extra: dict,
                    options: dict = {}, simulate: bool = False):

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

    def arb(self, routes: list[Route] = [],
            amount: int = 10,
            extras: list[dict] = []):

        # extras is a list of dictionaries
        assert len(routes) == len(extras), 'extra parameters must equal routes lenght'  # noqa E501
        Prospects = self.blockchain.genRoutes(
                        self.blockchain, routes=routes,
                        value=self.optimalAmount)

        for prospect in Prospects:
            pass

        try:
            for i in range(amount):
                prospect = anext(Prospects)

                if not extras:
                    payload = self.prepPayload(self, prospect, simulate=True)
                else:
                    payload = self.prepPayload(self, prospect,
                                               extras[i], simulate=True)

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
