'''The controller class that prepares and executes arbs'''

from scripts import CONFIG_PATH
import scripts.Errors as errors
from scripts.Models import (
    Token,
    Route,
    BaseBlockchain
)
from scripts.Utills import (
    readJson,
    profiler
    )
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
Price = dict[Token, int]


@attr.s
class Controller():
    blockchain: BaseBlockchain = attr.ib()
    testing: bool = attr.ib()
    pv: Optional[str] = attr.ib(default=os.environ.get('BEACON'))
    contractAbi: list = attr.ib(default=Config['ABIs']["ContractAbi"])
    routerAbi: list = attr.ib(default=Config['ABIs']["RouterAbi"])
    optimalAmount: float = attr.ib(default=1)  # 1.009027027)
    w3: Web3 = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        self.w3: Web3 = Web3(Web3.HTTPProvider(
                        self.blockchain.url, request_kwargs={'timeout': 300}))

    @property
    def swapFuncSig(self) -> str:
        return '0x38ed1739'  # swapExactTokensForTokens(uint256,uint256,address[],address,uint256) # noqa E501

    @property
    def approveFuncSig(self) -> str:
        return '0x095ea7b3'  # approve(address,uint256)

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

    @staticmethod
    def cumSum(listItem: list) -> list:
        result = [listItem[0]]
        for i in listItem[1:]:
            result.append(i * result[-1])
        return result

    def simSwap(self, route: Route,
                prices: list[dict[Token, int]]) -> int:
        In = route.capital

        for index, swap in enumerate(route.swaps):
            price = prices[index]

            Out = In * (self.blockchain.r1 * price[swap.to] /
                        price[swap.fro] / (1 + ((In/price[swap.fro])
                                                * self.blockchain.r1)))
            In = Out

        return int((Out - route.capital) * route.UsdValue)

    def calculate(self):
        pass

    @profiler
    def findAll(self, cache: dict, routes: list[Route],
                save: bool = True) -> list[Route]:

        print('finding arb \n')
        result = []
        r1 = self.blockchain.r1

        for route in routes:
            liquidity = []
            rates: list[float] = []
            _rates: list[float] = []
            prices: list[dict[Token, int]] = []

            for index, swap in enumerate(route.swaps):
                prices.append(cache[swap.via.pair])
                toPrice = cache[swap.via.pair][swap.to]
                froPrice = cache[swap.via.pair][swap.fro]
                toRate = r1 * toPrice / froPrice
                froRate = r1 * froPrice / toPrice
                if index == 0:
                    liquidity.append(froPrice)
                    forward = toPrice
                    rates.append(toRate)
                elif index == len(route.swaps) - 1:
                    rates.append(toRate * rates[-1])
                    liquidity += [min(froPrice, forward), toPrice]
                else:
                    rates.append(toRate * rates[-1])
                    liquidity.append(min(froPrice, forward))
                    forward = toPrice

                _rates.insert(0, froRate)

            least = min(liquidity)
            reverseLiq = liquidity[::-1]
            _rates = [1] + self.cumSum(_rates)
            rates = [1] + rates

            if rates[-1] > self.optimalAmount:
                route.capital = least / rates[liquidity.index(least)] * \
                    self.blockchain.impact
                route.EP = self.simSwap(route, prices)
                route.rates = rates

                result.append(route)
            elif _rates[-1] > self.optimalAmount:
                rroute = Route.toReverse(
                        _swaps=route.swaps,
                        UsdVal=route.UsdValue,
                        capital=least / _rates[reverseLiq.index(least)] *
                                self.blockchain.impact,  # noqa E131
                        rates=_rates
                    )
                rroute.EP = self.simSwap(rroute, prices[::-1])
                result.append(rroute)
        print('done!')
        return result

    def find(self, cache: dict,
             routes: list[Route] = []
             ) -> tuple[Route, int] | None:
        pass

    @staticmethod
    def prepPayload(route: Route):

        addresses, data = [], []
        amount = int(route.capital)
        pair = route.swaps[0].via.pair
        fee = route.swaps[0].via.fee
        out = route.rates[1]
        first_token_to = route.swaps[0].to
        first_token_fro = route.swaps[0].fro
        rem = route.swaps[1:]
        end = len(rem) - 1

        for index, i in enumerate(rem):

            # to populate the addresses list
            if index == 0 or rem[index - 1].via != i.via:
                addr = [i.fro.address, i.to.address]
                addresses.append(i.via.router)
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

        if self.testing:
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
                  amount: int = 5,
                  runs: int = 5,
                  frequency: int = 60,
                  mode: str = '') -> None:
        match mode:
            case 'live':
                pass
            case 'highest':
                pass
            case _:
                print('invalid mode')

        if not routes:
            pass
