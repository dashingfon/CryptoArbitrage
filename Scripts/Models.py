from abc import ABC, abstractmethod
from typing import Optional
from sqlmodel import Field, SQLModel
import attr


class RouteModel(SQLModel):
    simplyfied: str = Field()
    index: float = Field()
    capital: float = Field()
    EP: float = Field()
    USD_Value: float = Field()


@attr.s(slots=True)
class Route:
    swaps: list[dict[str, str]] = attr.ib(repr=False)
    prices: list[Optional[dict[str, str]]] = attr.ib(repr=False, factory=list)
    simplyfied: str = attr.ib(init=False)
    index: float = attr.ib(repr=False, default=0)
    capital: float = attr.ib(repr=False, default=0)
    EP: float = attr.ib(repr=False, default=0)
    USD_Value: float = attr.ib(repr=False, default=0)

    def __attrs_post_init__():
        pass

    def assemble(self):
        pass

    def simplyfy(self):
        pass

    @classmethod
    def toReversed(cls) -> 'Route':
        pass

    @classmethod
    def fromSimplifiedString(cls) -> 'Route':
        pass

    def toModel() -> RouteModel:
        pass


class TokenModel(SQLModel):
    name: str = Field()
    address: str = Field()
    price: float = Field()


@attr.s(frozen=True, slots=True)
class Token:
    name: str = attr.ib()
    address: str = attr.ib()

    def toModel() -> TokenModel:
        pass


class BaseBlockchain(ABC):

    @abstractmethod
    async def genRoutes(self):
        pass

    @abstractmethod
    async def pollRoutes(self):
        pass
