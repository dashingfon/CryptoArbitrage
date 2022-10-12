'''Model module containing the extra data type'''

from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator, Callable
from sqlmodel import Field, SQLModel
from cache import AsyncTTL
import attr
import time
import logging

Price = dict['Token', float]
GetRate = Callable[[Price, 'Token', 'Token', float], float]
getRate: GetRate = lambda price, to, fro, r1: r1 * price[to] / price[fro]  # noqa
# return self.r1 * price[to]/(1 + (self.impact * self.r1)) / price[fro]


@attr.s(slots=True, order=True, frozen=True)
class Token:
    '''Token class'''
    name: str = attr.ib(repr=False, order=False)
    address: str = attr.ib(repr=False, order=str.lower)

    @property
    def shortJoin(self) -> str:
        return f'{self.name}_{self.address[-7:]}'

    @property
    def fullJoin(self) -> str:
        return f'{self.name}_{self.address}'


@attr.s(slots=True)
class Swap():
    fro: Token = attr.ib()
    to: Token = attr.ib()
    via: str = attr.ib()


class Routes(SQLModel):
    '''Route Model class'''
    id: Optional[int] = Field(default=None, primary_key=True)
    simplyfied_Sht: str = Field()
    simplyfied_full: str = Field()
    startToken: str = Field(index=True)
    startExchanges: str = Field(index=True)
    amountOfSwaps: int = Field(index=True)
    time: float = Field(index=True)

    @classmethod
    def fromSwaps(cls, swaps: list[Swap]) -> 'Routes':

        short, long = [], []
        for j in swaps:
            long.append(f"{j.fro.fullJoin} {j.to.fullJoin} {j.via}")  # noqa: E501
            short.append(f"{j.fro.shortJoin} {j.to.shortJoin} {j.via}")  # noqa: E501

        return Routes(
           simplyfied_Sht=' - '.join(short),
           simplyfied_full=' - '.join(long),
           startToken=swaps[0].fro.shortJoin,
           startExchanges=swaps[0].via,
           amountOfSwaps=len(swaps),
           time=time.time()
        )


@attr.s(slots=True, order=True)
class Route:
    '''Route class'''
    swaps: list[Swap] = attr.ib(repr=False, order=False)
    prices: list[Price] = attr.ib(repr=False, factory=list, order=False)
    simplyfied: str = attr.ib(init=False, repr=False, order=False)
    simplyfied_short: str = attr.ib(init=False, order=False)
    USD_Value: float = attr.ib(default=0)
    EP: float = attr.ib(default=0)
    index: float = attr.ib(repr=False, default=0)
    capital: float = attr.ib(repr=False, default=0, order=False)

    def __attrs_post_init__(self) -> None:
        self.simplyfied = self.simplyfy()
        self.simplyfied_short = self.simplyfy(mode='short')

    def simplyfy(self, mode: str = 'long') -> str:
        '''function to generate a string repreentation
        from the swap attribute'''

        if mode != "long" or mode != 'short':
            raise ValueError(
                f"expected 'long' or 'short' got{mode}")

        result = []
        if mode == 'long':
            for j in self.swaps:
                result.append(f"{j.fro.fullJoin} {j.to.fullJoin} {j.via}")  # noqa: E501

        elif mode == 'short':
            for j in self.swaps:
                result.append(f"{j.fro.shortJoin} {j.to.shortJoin} {j.via}")  # noqa: E501

        return ' - '.join(result)

    @classmethod
    def toReversed(cls, items: list[Swap],
                   prices: list[Price]) -> 'Route':

        temp = cls(items[::-1])
        temp.prices = prices[::-1] if prices else []

        return temp

    @classmethod
    def fromFullString(cls, string: str, prices: list[dict] = [],
                       usdVal: float = 0, index: float = 0,
                       EP: float = 0,
                       capital: float = 0) -> 'Route':

        result: list = []
        routeList = string.split(' - ')
        for item in routeList:
            itemList = item.split()
            token1 = itemList[0].split('_')
            token2 = itemList[1].split('_')

            swap = Swap(
                fro=Token(token1[0], token1[1]),
                to=Token(token2[0], token2[1]),
                via=itemList[2]
            )
            result.append(swap)

        newRoute = cls(swaps=result)
        newRoute.prices = prices
        newRoute.USD_Value = usdVal
        newRoute.index = index
        newRoute.EP = EP
        newRoute.capital = capital

        return newRoute

    @staticmethod
    def cumSum(listItem: list) -> list:
        result = [listItem[0]]
        for i in listItem[1:]:
            result.append(i*result[-1])
        return result

    def simSwap(self, r1: float) -> float:

        assert self.capital, 'route object has no capital set'
        assert len(self.prices) == len(self.swaps), 'unequal route and prices'
        In = self.capital

        for index, swap in enumerate(self.swaps):
            price = self.prices[index]

            Out = In * getRate(
                price,
                swap.to,
                swap.fro, r1) / (1 + ((In/price[swap.fro]) * r1))
            In = Out

        return Out - self.capital

    def calculate(self, r1: float,
                  impact: float,
                  usdVal: float) -> list['Route']:

        rates: list[list[float]] = [[], []]
        liquidity = []
        reverse: 'Route' = self.toReversed(self.swaps, self.prices)

        if not self.prices:
            return [self, reverse]

        for index, swap in enumerate(self.swaps):
            price: Price = self.prices[index]

            rate = (getRate(price, swap.to, swap.fro, r1),
                    getRate(price, swap.fro, swap.to, r1))

            if index == 0:
                liquidity.append(price[swap.fro])
                forward = price[swap.to]
                rates[0].append(rate[0])
            elif index == len(self.swaps) - 1:
                rates[0].append(rate[0] * rates[0][-1])
                liquidity += [
                    min(price[swap.fro], forward), price[swap.to]]
            else:
                rates[0].append(rate[0] * rates[0][-1])
                liquidity.append(min(price[swap.fro], forward))
                forward = price[swap.to]

            rates[1].insert(0, rate[1])

        least = min(liquidity)
        reverseLiq = liquidity[::-1]
        rates[1] = [1] + self.cumSum(rates[1])
        rates[0] = [1] + rates[0]

        self.capital = least / rates[0][liquidity.index(least)] * impact * 1e18
        reverse.capital = least / rates[1][reverseLiq.index(least)] * impact * 1e18  # noqa: E501

        toEp, froEp = self.simSwap(r1), reverse.simSwap(r1)

        self.EP, reverse.EP = toEp * 1e18, froEp * 1e18
        self.index, reverse.index = rates[0][-1], rates[1][-1]
        self.USD_Value, reverse.USD_Value = toEp * usdVal, froEp * usdVal

        return [self, reverse]


class BaseBlockchain(ABC):
    '''Base blockchain implementation'''
    url: str

    @property
    def arbAddress(self) -> Optional[str]:
        pass

    @abstractmethod
    async def genRoutes(self, value: float,
                        routes: list[Route] = [],
                        **kwargs: dict) -> AsyncGenerator:

        pass


class Spliter:
    '''iterator class for spliting a list into batches'''
    def __init__(self, items: list, cache: AsyncTTL,
                 start: int = 0, gap: int = 1) -> None:

        self.cache: AsyncTTL = cache
        self.items: list = items
        self.start: int = start
        self.end: int = self.start + gap

        logging.info(f'Spliter class; List lenght :- {len(self.items)}')
        logging.info(f'start :- {start} gap :- {gap}')

    def __iter__(self) -> 'Spliter':
        return self

    def __next__(self) -> list[Route]:
        if self.start < len(self.items):
            cacheLenght = len(self.cache.ttl)
            start = self.start
            gap = self.end - self.start

            if cacheLenght <= 4 and gap > 1:
                gap = 1
            elif 5 <= cacheLenght <= 8 and gap > cacheLenght // 4:
                gap = cacheLenght // 4
            elif 6 <= cacheLenght <= 12 and gap > cacheLenght // 3:
                gap = cacheLenght // 3
            elif 12 <= cacheLenght <= 30 and gap > cacheLenght // 2:
                gap = cacheLenght // 2

            logging.info(f'gap :- {gap} start :- {start}')

            self.start += gap
            self.end = self.start + gap * 2
            return self.items[start:start + gap]
        else:
            raise StopIteration
