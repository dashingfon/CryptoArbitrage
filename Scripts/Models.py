'''Model module containing the extra data type'''

from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator
from sqlmodel import Field, SQLModel
from cache import AsyncTTL
import attr
import logging


@attr.s(slots=True)
class Token:
    '''Token class'''
    name: str = attr.ib(repr=False)
    address: str = attr.ib(repr=False)
    shortJoin: str = attr.ib(init=False)
    fullJoin: str = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self) -> None:
        self.shortJoin = f'{self.name}_{self.address[-7:]}'
        self.fullJoin = f'{self.name}_{self.address}'

    '''def __hash__(self) -> int:
        return int(self.address)
'''
    '''def __attrs_post_init__(self) -> None:
        self.join = f"{self.name}_{self.address[-7:]}"'''


class Routes(SQLModel, table=True):
    '''Route Model class'''
    id: Optional[int] = Field(default=None, primary_key=True)
    simplyfied_Sht: str = Field()
    simplyfied_full: str = Field()
    startToken: str = Field(index=True)
    startExchanges: str = Field(index=True)
    amountOfSwaps: int = Field(index=True)
    time: float = Field(index=True)

    @classmethod
    def fromString(cls, string):
        pass


@attr.s(slots=True)
class Route:
    '''Route class'''
    swaps: list[dict[str, Token | str]] = attr.ib(repr=False)
    prices: list[Optional[dict[str, str]]] = attr.ib(repr=False, factory=list)
    simplyfied: str = attr.ib(init=False, repr=False)
    simplyfied_short: str = attr.ib(init=False)
    index: float = attr.ib(repr=False, default=0)
    capital: float = attr.ib(repr=False, default=0)
    EP: float = attr.ib(default=0)
    USD_Value: float = attr.ib(default=0)

    def __attrs_post_init__(self) -> None:
        self.simplyfied = self.simplyfy()
        self.simplyfied_short = self.simplyfy(mode='short')

    def simplyfy(self, mode: str = 'long') -> str:
        '''function to generate a tring repreentation from the wap attribute'''

        if mode == 'long':
            pass
        elif mode == 'short':
            pass

        result = [f"{self.swaps[0]['from']} {self.swaps[0]['to']} {self.swaps[0]['via']}"]  # noqa: E501
        for j in self.swaps[1:]:
            result.append(f"{j['from']} {j['to']} {j['via']}")

        return ' - '.join(result)

    @classmethod
    def toReversed(cls, items: list[dict[str, Token | str]],
                   prices: list[Optional[dict[str, str]]]) -> 'Route':

        temp = cls(items[::-1])
        temp.prices = prices[::-1] if prices else []

        return temp

    @classmethod
    def fromFullString(cls, string: str) -> 'Route':
        result: list = []
        routeList = string.split(' - ')
        for item in routeList:
            itemList = item.split()
            token1 = itemList[0].split('_')
            token2 = itemList[1].split('_')

            load = {
                'from': Token(token1[0], token1[1]),
                'to': Token(token2[0], token2[1]),
                'via': itemList[2],
                }
            result.append(load)

        return cls(swaps=result)

    def toWei(self) -> None:
        pass

    def fromWei(self) -> None:
        pass


class BaseBlockchain(ABC):
    '''Base blockchain implementation'''

    @abstractmethod
    async def genRoutes(self, value: float,
                        routes: Optional[list[Route]] = [],
                        **kwargs: dict) -> AsyncGenerator:  # type ignore
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
