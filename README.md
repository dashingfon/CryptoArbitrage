> # Crypto Arbitrage Project
### A Decentralized finance (defi) Arbitrage Bot

Crypto Arbitrage is an arbitrage bot that spots the price discrepancies accross EVM compatible decentralized exchanges and trades using smart contracts
CryptoArbitrage implement flash loans to maximize the potential profit


## Basic Usage

*main.py*
```python

import scripts.Blockchains as Blc
import scripts.Controller as Ctr
import asyncio

'''
please note for windows you can suppress the proactor event loop closed error with

'
from asyncio.proactor_events import _ProactorBasePipeTransport
from scripts.utills import silence_event_loop_closed
_ProactorBasePipeTransport.__del__ = silence_event_loop_closed(
    _ProactorBasePipeTransport.__del__)
'
'''

# The main function

async def main():

    url = 'https://bsc-dataseed.binance.org'
    Chain = Blc.BSC(url)
    Controller = Ctr(Chain)

    await Controller.arb()


if __name__ == '__main__':
    asyncio.run(main())

```

To just poll the routes without making any trades

*main.py*
```python
# importing the required classes

import scripts.Blockchains as Blc

# The main function
async def main():
    await Blc.BSC().pollRoutes()
    # it will generate a poll report file in the data folder


if __name__ == '__main__':
    asyncio.run(main())
```

<img align="left" width="26px" src="https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white"/>

<img align="left" width="26px" src="https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue"/>

<img align="left" width="26px" src="https://img.shields.io/badge/Solidity-e6e6e6?style=for-the-badge&logo=solidity&logoColor=black"/>

<img align="left" width="26px" src="https://img.shields.io/badge/GIT-E44C30?style=for-the-badge&logo=git&logoColor=white"/>




[^note]:
    Named footnotes will still render with numbers instead of the text but allow easier identification and linking.  
    This footnote also has been made with a different syntax using 4 spaces for new lines.