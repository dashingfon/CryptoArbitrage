from abc import ABC, abstractmethod
from typing import Optional, Any, AsyncGenerator
from sqlmodel import Field, SQLModel
from cache import AsyncTTL
import attr


@attr.s(slots=True, frozen=True)
class Token:
    name: str = attr.ib(repr=False)
    address: str = attr.ib(repr=False)
    join: str = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        pass


class RouteModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    simplyfied_Sht: str = Field()
    simplyfied_full: str = Field()
    startToken: str = Field(index=True)
    startExchanges: str = Field(index=True)
    amountOfSwaps: int = Field(index=True)
    index: float = Field()
    capital: float = Field()
    EP: float = Field()
    USD_Value: float = Field()
    time: float = Field()


@attr.s(slots=True)
class Route:
    swaps: list[dict[str, Token]] = attr.ib(repr=False)
    prices: list[Optional[dict[str, str]]] = attr.ib(repr=False, factory=list)
    simplyfied: str = attr.ib(init=False)
    index: float = attr.ib(repr=False, default=0)
    capital: float = attr.ib(repr=False, default=0)
    EP: float = attr.ib(repr=False, default=0)
    USD_Value: float = attr.ib(repr=False, default=0)

    def __attrs_post_init__(self) -> None:
        self.simplyfied = self.simplyfy()

    def assemble(self) -> list[dict[str, Token]]:
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

    def simplyfy(self) -> str:
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

    def toModel(self) -> RouteModel:
        pass

    def convert(self) -> None:
        pass


class BaseBlockchain(ABC):

    @abstractmethod
    async def genRoutes(self, **kwargs: Any) -> AsyncGenerator:  # type ignore
        pass

    '''@abstractmethod
    async def pollRoutes(self, batch: int, routes: list, save: bool,
                         currentPrice: bool, value: float):
        pass
    '''


class Spliter:
    def __init__(self, items: list, cache: AsyncTTL,
                 start: int = 0, gap: int = 1) -> None:

        self.cache: AsyncTTL = cache
        self.items: list = items
        self.start: int = start
        self.end: int = self.start + gap

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

            self.start += gap
            self.end = self.start + gap * 2
            return self.items[start:start + gap]
        else:
            raise StopIteration
