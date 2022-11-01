'''Model module containing the extra data type'''

from typing import (
    Callable,
    Protocol
    )
import attr

Price = dict['Token', float]
GetRate = Callable[[Price, 'Token', 'Token', float], float]
getRate: GetRate = lambda price, to, fro, r1: r1 * price[to] / price[fro]  # noqa
# return self.r1 * price[to]/(1 + (self.impact * self.r1)) / price[fro]


@attr.s(slots=True, order=True, frozen=True)
class Token:
    '''Token class'''
    name: str = attr.ib(repr=True, order=False)
    address: str = attr.ib(repr=True, order=str.lower)

    @property
    def shortJoin(self) -> str:
        return f'{self.name}_{self.address.lower()[-7:]}'

    @property
    def fullJoin(self) -> str:
        return f'{self.name}_{self.address}'


@attr.s(slots=True)
class Via():
    name: str = attr.ib()
    pair: str = attr.ib()
    fee: float = attr.ib()
    router: str = attr.ib()


@attr.s(slots=True, frozen=True)
class Swap():
    fro: Token = attr.ib()
    to: Token = attr.ib()
    via: Via = attr.ib()


@attr.s(slots=True, order=True)
class Route:
    '''Route class'''
    swaps: list[Swap] = attr.ib(repr=False, order=False)
    simplyfied_short: str = attr.ib(init=False, order=False)
    UsdValue: float = attr.ib()
    EP: float = attr.ib(default=0)
    rates: list = attr.ib(factory=list)
    capital: float = attr.ib(default=0, order=False)

    def __attrs_post_init__(self) -> None:
        self.simplyfied_short = self.simplyfy()

    def simplyfy(self, swaps: list = []) -> str:
        '''function to generate a string repreentation
        from the swap attribute'''

        if not swaps:
            swaps = self.swaps

        result = []
        for j in swaps:
            result.append(f"{j.fro.shortJoin} {j.to.shortJoin} {j.via.name}")  # noqa: E501

        return ' - '.join(result)

    def reverseSimplyfied(self) -> str:
        swaps = []
        for s in self.swaps[::-1]:
            swaps.append(Swap(
                fro=s.to,
                to=s.fro,
                via=s.via
            ))
        return self.simplyfy(swaps)

    @classmethod
    def fromDict(cls, load):
        swaps = []
        for swap in load.get('swaps'):
            swaps.append(
                Swap(
                    fro=Token(**(swap.get('fro'))),
                    to=Token(**(swap.get('to'))),
                    via=Via(**(swap.get('via')))
                )
            )
        return cls(
            swaps=swaps,
            EP=load.get('EP'),
            UsdValue=load.get('UsdValue'),
            rates=load.get('rates'),
            capital=load.get('capital')
        )

    @classmethod
    def toReverse(cls, _swaps: list[Swap], UsdVal, **kwargs):
        swaps = []
        for s in _swaps[::-1]:
            swaps.append(Swap(
                fro=s.to,
                to=s.fro,
                via=s.via
            ))

        return cls(
            swaps=swaps,
            UsdValue=UsdVal,
            **kwargs
        )


class BaseBlockchain(Protocol):

    url: str = ''
    exchanges: dict = {}
    r1: float
    impact: float

    @property
    def arbAddress(self) -> str:
        return ''

    async def buildCache(self, routes: list[Route]) -> dict[str, Price]:
        pass


class Spliter:

    def __init__(self, items: list,
                 start: int, gap: int) -> None:

        self.items = items
        self.start = start
        self.end = self.start + gap

    def __iter__(self) -> 'Spliter':
        return self

    def __next__(self) -> list[Route]:

        if self.start < len(self.items):
            start = self.start
            gap = self.end - self.start
            self.start += gap
            self.end = self.start + gap * 2
            return self.items[start:start + gap]
        else:
            raise StopIteration
