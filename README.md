> # Crypto-Arbitrage Project
### A Decentralized finance (defi) Arbitrage Bot

Crypto-Arbitrage is an arbitrage bot that spots the price discrepancies accross EVM compatible decentralized exchanges and trades using smart contracts
CryptoArbitrage implements flash loans to maximize the potential profit

## Dependencies

Crypto-Arbitrage depends on the following packages and installations

* Web3.py (requires Microsoft Visual C++ 14.0 or greater on windows)
* brownie (requires ganache-cli and python 3.6 and above)
* brownie eth-pm OpenZeppelin/openzeppelin-contracts@4.4.0

## Initialization

After installing the main requirements(in requirements_main.txt) in a virtual environment, initialize a brownie project with;

*terminal*
```shell

brownie init
```

pull and merge this repository into your directory with;

*terminal*
```shell

git init
git remote add origin https://the-link
git pull origin main --allow-unrelated-histories

```

run the setup for any Blockchain of your choice(or all)

*main.py*
```python

import scripts.Blockchains as Blc

Arbitrum = Blc.Arbitrum()
Arbitrum.setup()

```

create a .env file in the parent directory and set your private key

*.env*
```.env
export BEACON=0x00000000000000000000000PRIVATE0000000KEY000000

```

or alternatively create a new account with brownie

then to deploy the arbitrage contract

*main.py*
```python

from brownie import BscArb, accounts

# the Binance smart chain is the only chain with a completed Arbitrage contract


def main():
    privKey = os.environ.get('BEACON')
    BscArb.deploy({'from': self.web3.eth.account.from_key(privKey)})

if __name__ == '__main__':
    main()

```
## Basic Usage

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

async def arb():

    url = 'https://bsc-dataseed.binance.org'
    Chain = Blc.BSC(url)
    Controller = Ctr(Chain)

    await Controller.arb(amount=5)
    
    # This executes the first five arbitrage trades found
    # default is set to 10


if __name__ == '__main__':
    asyncio.run(arb())

```

To just poll the routes without making any trades

*main.py*
```python

import scripts.Blockchains as Blc

async def poll():
    pollResult = await Blc.BSC().pollRoutes(save=False)
    print(pollResult)
    
    # this polls the routes and returns the result in json
    # it will generate a pollReport file in the data folder if save=True

if __name__ == '__main__':
    asyncio.run(poll())

```

## Tests

To run the tests, install the dependencies in the requirements.txt file, then in the parent directory run

```cmd

pytest tests

```


<div>
<img align="left" width="30px" src="https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white"/>

<img align="left" width="30px" src="https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue"/>

<img align="left" width="30px" src="https://img.shields.io/badge/Solidity-e6e6e6?style=for-the-badge&logo=solidity&logoColor=black"/>

<img align="left" width="30px" src="https://img.shields.io/badge/GIT-E44C30?style=for-the-badge&logo=git&logoColor=white"/>
</div>

<div>
*Please Note*:
Crypto-Arbitrage is still in active development, some of the functionalities have not been extensively tested
</div>