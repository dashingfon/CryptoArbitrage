'''The controller class that prepares and executes arbs'''

from scripts import CONFIG_PATH
import scripts.Errors as errors
from scripts.Models import (
    BaseBlockchain,
    Route
)
from scripts.Utills import readJson

import os
import attr
import logging
from web3 import Web3
from typing import (
    Any,
    Optional,
    )
from eth_abi import encode_abi
from dotenv import load_dotenv


load_dotenv()
Config: dict = readJson(CONFIG_PATH)


@attr.s
class Controller():
    blockchain: BaseBlockchain = attr.ib()

    @blockchain.validator
    def verifyChain(self, attribute, value) -> None:
        if not value.url:
            raise errors.EmptyBlockchainUrl(
                'Blockchain Objects url is empty')

    testing: bool = attr.ib()
    pv: Optional[str] = attr.ib(default=os.environ.get('BEACON'))
    contractAbi: list = attr.ib(default=Config['ABIs']["ContractAbi"])
    routerAbi: list = attr.ib(default=Config['ABIs']["RouterAbi"])
    optimalAmount: float = attr.ib(default=1.009027027)
    w3: Web3 = attr.ib(default=(Web3(Web3.HTTPProvider(
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
        return self.w3.eth.contract(address=address, abi=abi)  # type: ignore

    def getAccount(self) -> Any:
        if self.testing:
            return self.w3.eth.accounts[0]
        elif not self.pv:
            raise errors.PrivateKeyNotSet('no private key set')
        else:
            return self.w3.eth.account.from_key(self.pv)

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

    def prepPayload(self, route: Route, routers: list = [],
                    pair: str = '', fee: float = 0.,
                    out: float = 0.):

        addresses, data = [], []
        amount = int(route.capital)

        first_token_to = route.swaps[0].to
        first_token_fro = route.swaps[0].fro
        rem = route.swaps[1:]
        end = len(rem) - 1

        if routers and len(routers) != len(route.swaps):
            raise errors.UnequalRouteAndRouters(
                'route and routers have unequal lenght')
        elif not routers:
            routers = []
            for swap in route.swaps:
                routers.append(
                    self.blockchain.exchanges[swap.via]['router'])

        if not pair:
            pair = self.blockchain.exchanges[swap.via]['pairs'][
                        frozenset([first_token_to, first_token_fro])]

        if not fee:
            fee = self.blockchain.exchanges[swap.via]['fee']

        for index, i in enumerate(rem):
            router = routers[index + 1]

            # to populate the addresses list
            if index == 0 or rem[index - 1].via != i.via:
                addr = [i.fro.address, i.to.address]
                addresses.append(router)
                print(f'addresses snapshot, index {index} :- {addresses}')
            else:
                addr.append(i.to.address)

            # to populate the data list
            if index == end or rem[index + 1].via != i.via:
                defs: list[str] = ['address[]']
                args: list[Any] = [addr]
                print(f'addr snapshot, index {index} :- {addr}')
                data.append(encode_abi(defs, args))

        defs = ['address[]', 'bytes[]', 'address', 'uint256', 'uint256']
        args = [addresses, data, pair, amount, fee]

        # print(args)
        DATA = Web3.toHex(encode_abi(defs, args))
        token0 = sorted([first_token_fro, first_token_to])[0]

        if not out:
            start = self.getAmountsOut(
                    routers[0], amount,
                    [first_token_fro.address, first_token_to.address])
        else:
            start = int(out)

        AMOUNT0 = start if first_token_fro.address == token0 else 0
        AMOUNT1 = 0 if first_token_fro.address == token0 else start

        # print(f'final payload :- {AMOUNT0,AMOUNT1,tokens[names[0]],DATA}')

        return {
            'profitable': None,
            'data': [AMOUNT0, AMOUNT1, first_token_fro.address, DATA]}

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

    async def arb(self, routes: list[Route] = [],
                  amount: int = 10,
                  extras: list[dict] = []):

        # extras is a list of dictionaries
        assert len(routes) == len(extras), 'extra parameters must equal routes lenght'  # noqa E501
        Prospects = await self.blockchain.genRoutes(
                        routes=routes,
                        value=self.optimalAmount)

        count = 0
        async for prospect in Prospects:
            if not count < amount:
                break

            prospect = await anext(Prospects)

            if not extras:
                payload = self.prepPayload(prospect)
            else:
                payload = self.prepPayload(prospect, **extras[count])

            if payload['profitable']:
                self.execute(payload['data'])

            count += 1
