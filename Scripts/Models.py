'''Model module containing the extra data type'''

from abc import ABC, abstractmethod
from typing import Optional, Any, AsyncGenerator
from sqlmodel import Field, SQLModel
from cache import AsyncTTL
import attr
import logging


@attr.s(slots=True, frozen=True)
class Token:
    '''Token class'''
    name: str = attr.ib(repr=False)
    address: str = attr.ib(repr=False)
    shortjoin: str = attr.ib(init=False)
    fulljoin: str = attr.ib(init=False, repr=False)

    def __attrs_post_init__(self) -> None:
        self.shortJoin = f'{name}_{address[-7:]}'
        self.fullJoin = f'{name}_{address}'

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
    swaps: list[dict[str, Token]] = attr.ib(repr=False)
    prices: list[Optional[dict[str, str]]] = attr.ib(repr=False, factory=list)
    simplyfied: str = attr.ib(init=False, repr=False)
    simplyfied_short: str = attr.ib(init=False)
    index: float = attr.ib(repr=False, default=0)
    capital: float = attr.ib(repr=False, default=0)
    EP: float = attr.ib(repr=False, default=0)
    USD_Value: float = attr.ib(repr=False, default=0)

    def __attrs_post_init__(self) -> None:
        self.simplyfied = self.simplyfy()
        self.simplyfied_short

    def assemble(self) -> list[dict[str, Token]]:
        '''function to aemble the swap atribute from string'''
        result = []
        routeList = self.simplyfied.split(' - ')
        for item in routeList:
            itemList = item.split()
            load = {
                'from': itemList[0],
                'to': itemList[1],
                'via': itemList[2],
                }
            result.append(load)
        return result

    def simplyfy(self, mode: str = 'long') -> str:
        '''function to generate a tring repreentation from the wap attribute'''
        match mode:
            case 'long':
                break
            case 'short':
                break

        result = [f"{self.swaps[0]['from']} {self.swaps[0]['to']} {self.swaps[0]['via']}"]  # noqa: E501
        for j in self.swaps[1:]:
            result.append(f"{j['from']} {j['to']} {j['via']}")
        
        return ' - '.join(result)

    @classmethod
    def toReversed(cls, items: list[dict[str, Token]],
                   prices: list[Optional[dict[str, str]]]) -> 'Route':

        temp = cls(items[::-1])
        if prices:
            temp.prices = prices[::-1]
        return temp

    @classmethod
    def fromFullString(cls, string: str) -> 'Route':
        pass

    def convert(self) -> None:
        pass


class BaseBlockchain(ABC):
    '''Base blockchain implementation'''
    url: str
    arbAddress: str

    @abstractmethod
    async def genRoutes(self, **kwargs: Any) -> AsyncGenerator:  # type ignore
        pass

    '''@abstractmethod
    async def pollRoutes(self, batch: int, routes: list, save: bool,
                         currentPrice: bool, value: float):
        pass
    '''


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
