> # Crypto Arbitrage Project
### A Decentralized finance (defi) Arbitrage Bot

Crypto Arbitrage is an arbitrage bot that spots the price discrepancies accross EVM compatible decentralized exchanges and trades using smart contracts
CryptoArbitrage implement flash loans to maximize the potential profit


## Initialization

To begin, deploy the arb contract

```python

import brownie

def deploy():
    pass

def main():
    pass

```
## Basic Usage

After deploying the arbitrage contract


*main.py*
```python

 # to import the reauired classes and modules

import scripts.Blockchains as Blc
import scripts.Controller as Ctr
import asyncio

```

*Note:* 
For windows you can suppress the proactor event loop closed error with

```python

from asyncio.proactor_events import _ProactorBasePipeTransport
from scripts.utills import silence_event_loop_closed

_ProactorBasePipeTransport.__del__ = silence_event_loop_closed(
    _ProactorBasePipeTransport.__del__)

```

To poll the routes and execute any profitable swaps

*main.py*
```python

async def main():

    url = 'https://bsc-dataseed.binance.org'
    Chain = Blc.BSC(url)
    Controller = Ctr(Chain)

    await Controller.arb(amount = 5)
    
    # This executes the first five arbitrage trades found
    # default is set to 10


if __name__ == '__main__':
    asyncio.run(main())

```

To just poll the routes without making any trades

*main.py*
```python

import scripts.Blockchains as Blc

async def main():
    pollResult = await Blc.BSC().pollRoutes(save=False)
    print(pollResult)
    
    # this polls the routes and returns the result in json
    # it will generate a pollReport file in the data folder if save=True

if __name__ == '__main__':
    asyncio.run(main())
```

<img align="left" width="26px" src="https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white"/>

<img align="left" width="26px" src="https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue"/>

<img align="left" width="26px" src="https://img.shields.io/badge/Solidity-e6e6e6?style=for-the-badge&logo=solidity&logoColor=black"/>

<img align="left" width="26px" src="https://img.shields.io/badge/GIT-E44C30?style=for-the-badge&logo=git&logoColor=white"/>


