
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

    liquidity = []
    selfRates: list[float] = []
    reverseRates: list[float] = []
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
            selfRates.append(rate[0])
        elif index == len(self.swaps) - 1:
            selfRates.append(rate[0] * selfRates[-1])
            liquidity += [
                min(price[swap.fro], forward), price[swap.to]]
        else:
            selfRates.append(rate[0] * selfRates[-1])
            liquidity.append(min(price[swap.fro], forward))
            forward = price[swap.to]

        reverseRates.insert(0, rate[1])

    least = min(liquidity)
    reverseLiq = liquidity[::-1]
    reverseRates = [1] + self.cumSum(reverseRates)
    selfRates = [1] + selfRates

    self.capital = least / selfRates[liquidity.index(least)] * impact * 1e18  # noqa: E501
    reverse.capital = least / reverseRates[reverseLiq.index(least)] * impact * 1e18  # noqa: E501

    toEp, froEp = self.simSwap(r1), reverse.simSwap(r1)

    self.EP, reverse.EP = toEp * 1e18, froEp * 1e18
    self.index, reverse.index = selfRates[-1], reverseRates[-1]
    self.USD_Value, reverse.USD_Value = toEp * usdVal, froEp * usdVal

    return [self, reverse]
