# Configuration file containing the blockchain settings
# Controller Settings

import json


def parseEchanges(item):
    new = {}
    try:
        for key, value in item.items():
            temp = {}
            new[key] = value
            for i, j in value['pairs'].items():
                temp[frozenset(i.split(' - '))] = j
            new[key]['pairs'] = temp
    except KeyError as e:
        print(f'incorrect exchange data, KeyError :- {e}')
    return new


with open(r'scripts\Config.json') as CJ:
    config = json.load(CJ)

ControllerBlockchains = set((
    'Binance SmartChain',
    'Aurora Blockchain',
    'Kovan Testnet',
))

T1 = config['Test']['T1']
T2 = config['Test']['T2']
T3 = config['Test']['T3']
T4 = config['Test']['T4']

fonswapRouter = config['Test']['fonswapRouter']
dodoRouter = config['Test']['dodoRouter']
contract = config['Test']['contract']

cap = config['Test']['cap']
f = config['Test']['f']
l = config['Test']['l']

PAIR = config['Test']['PAIR']
factory = config['Test']['factory']
fee = config['Test']['fee']
amount = int(cap * f)

routerAbi = config['ABIs']['Router_abi']
contractAbi = config['ABIs']['Contract_abi']


OPTIONS = [
    {'tokens' : {'TST1' : T1,'TST2' : T2,'TST3' : T3,'TST4' : T4},
    'pair' : PAIR,
    'out' : f,
    'factory' : factory,
    'routers' : [fonswapRouter,fonswapRouter,fonswapRouter,fonswapRouter],
    'fee' : fee},

    {'tokens' : {'TST1' : T1,'TST2' : T2,'TST3' : T3,'TST4' : T4},
    'pair' : PAIR,
    'out' : f,
    'factory' : factory,
    'routers' : [fonswapRouter,dodoRouter,dodoRouter,fonswapRouter],
    'fee' : fee},
    
    {'tokens' : {'TST1' : T1,'TST2' : T2,'TST3' : T3,'TST4' : T4},
    'pair' : PAIR,
    'out' : f,
    'factory' : factory,
    'routers' : [fonswapRouter,fonswapRouter,dodoRouter,dodoRouter],
    'fee' : fee},

    {'tokens' : {'TST1' : T1,'TST2' : T2,'TST3' : T3,'TST4' : T4},
    'pair' : PAIR,
    'out' : f,
    'factory' : factory,
    'routers' : [fonswapRouter,dodoRouter,fonswapRouter,dodoRouter],
    'fee' : fee},

    ]

ITEMS = [
    {
        'EP' : cap * (l - 1), 'capital' : cap,
        'simplified' : "TST4 TST2 fonswap - TST2 TST3 fonswap - TST3 TST1 fonswap - TST1 TST4 fonswap",
        'route' : [{'from': 'TST4', 'to': 'TST2', 'via': 'fonswap'}, {'from': 'TST2', 'to': 'TST3', 'via': 'fonswap'}, {'from': 'TST3', 'to': 'TST1', 'via': 'fonswap'},{'from': 'TST1', 'to': 'TST4', 'via': 'fonswap'}] ,
    },
    {
        'EP' : cap * (l - 1), 'capital' : cap,
        'simplified' : "TST4 TST2 fonswap - TST2 TST3 dodo - TST3 TST1 dodo - TST1 TST4 fonswap",
        'route' : [{'from': 'TST4', 'to': 'TST2', 'via': 'fonswap'}, {'from': 'TST2', 'to': 'TST3', 'via': 'dodo'}, {'from': 'TST3', 'to': 'TST1', 'via': 'dodo'},{'from': 'TST1', 'to': 'TST4', 'via': 'fonswap'}] ,
    },
    {
        'EP' : cap * (l - 1), 'capital' : cap,
        'simplified' : "TST4 TST2 fonswap - TST2 TST3 fonswap - TST3 TST1 fonswap - TST1 TST4 fonswap",
        'route' : [{'from': 'TST4', 'to': 'TST2', 'via': 'fonswap'}, {'from': 'TST2', 'to': 'TST3', 'via': 'fonswap'}, {'from': 'TST3', 'to': 'TST1', 'via': 'dodo'},{'from': 'TST1', 'to': 'TST4', 'via': 'dodo'}] ,
    },
    {
        'EP' : cap * (l - 1), 'capital' : cap,
        'simplified' : "TST4 TST2 fonswap - TST2 TST3 fonswap - TST3 TST1 fonswap - TST1 TST4 fonswap",
        'route' : [{'from': 'TST4', 'to': 'TST2', 'via': 'fonswap'}, {'from': 'TST2', 'to': 'TST3', 'via': 'dodo'}, {'from': 'TST3', 'to': 'TST1', 'via': 'fonswap'},{'from': 'TST1', 'to': 'TST4', 'via': 'dodo'}] ,
    },
]

PREPARED = []
for i in range(len(OPTIONS)):
    PREPARED.append([amount,0,T4,config['Test']['PrepedSwapData'][i]])

assert len(OPTIONS) == len(ITEMS) == len(PREPARED)

PACKAGES = []
for i in range(len(OPTIONS)):
    PACKAGES.append((OPTIONS[i],ITEMS[i],PREPARED[i]))




# Aurora Network

AuroraTokens = {
    'NEAR' : '0xc42c30ac6cc15fac9bd938618bcaa1a1fae8501d',
    'USDC' : '0xb12bfca5a55806aaf64e99521918a4bf0fc40802',
    'USDT' : '0x4988a896b1227218e4a686fde5eabdcabd91571f',
    'atUST' : '0x5ce9f0b6afb36135b5ddbf11705ceb65e634a9dc',
    'DAI' : '0xe3520349f477a5f6eb06107066048508498a291b',
    'WETH' : '0xc9bdeed33cd01541e1eed10f90519d2c06fe3feb',
    'WBTC' : '0xf4eb217ba2454613b15dbdea6e5f22276410e89e',
    'AURORA' : '0x8bec47865ade3b172a928df8f990bc7f2a3b9f79',
    
}
AuroraStartTokens = ['USDT', 'USDC', 'NEAR', 'WETH']
AuroraStartExchanges = ['dodo']
AuroraExchanges = {
    'trisolaris' : {
        'pairs' : {
        frozenset(('AURORA', 'WETH')) : '0x5eeC60F348cB1D661E4A5122CF4638c7DB7A886e',
        frozenset(('NEAR', 'WETH')) : '0x63da4DB6Ef4e7C62168aB03982399F9588fCd198',
        frozenset(('NEAR', 'USDC')) : '0x20F8AeFB5697B77E0BB835A8518BE70775cdA1b0',
        frozenset(('NEAR', 'USDT')) : '0x03B666f3488a7992b2385B12dF7f35156d7b29cD',
        frozenset(('USDC', 'USDT')) : '0x2fe064B6c7D274082aa5d2624709bC9AE7D16C77',
        frozenset(('NEAR', 'WBTC')) : '0xbc8A244e8fb683ec1Fd6f88F3cc6E565082174Eb',
        frozenset(('AURORA', 'NEAR')) : '0x1e0e812FBcd3EB75D8562AD6F310Ed94D258D008',
        },
        'router' : '0x2CB45Edb4517d5947aFdE3BEAbF95A582506858B',
        'factory' : '',
        'fee': 0
    },

    'auroraswap' : {
        'pairs' : {
        frozenset(('USDT', 'USDC')) : '0xec538fafafcbb625c394c35b11252cef732368cd',
        frozenset(('USDC', 'NEAR')) : '0x480a68ba97d70495e80e11e05d59f6c659749f27',
        frozenset(('USDT', 'NEAR')) : '0xf3de9dc38f62608179c45fe8943a0ca34ba9cefc',
        frozenset(('NEAR', 'WETH')) : '0xc57ecc341ae4df32442cf80f34f41dc1782fe067',
        frozenset(('WETH', 'WBTC')) : '0xcb8584360dc7a4eac4878b48fb857aa794e46fa8'
        },
        'router' : '0xA1B1742e9c32C7cAa9726d8204bD5715e3419861',
        'factory' : '',
        'fee': 0
    },

    'wannaswap' : {
        'pairs' : {
        frozenset(('AURORA', 'NEAR')) : '0x7e9ea10e5984a09d19d05f31ca3cb65bb7df359d',
        frozenset(('NEAR', 'WBTC')) : '0xbf58062d23f869a90c6eb04b9655f0dfca345947',
        frozenset(('NEAR', 'WETH')) : '0x256d03607eee0156b8a2ab84da1d5b283219fe97',
        frozenset(('USDC', 'NEAR')) : '0xbf560771b6002a58477efbcdd6774a5a1947587b',
        frozenset(('USDT', 'NEAR') ): '0x2e02bea8e9118f7d2ccada1d402286cc6d54bd67',
        frozenset(('WETH', 'WBTC')) : '0xf56997948d4235514dcc50fc0ea7c0e110ec255d',
        frozenset(('USDT', 'USDC')) : '0x3502eac6fa27beebdc5cd3615b7cb0784b0ce48f'
        },
        'router' : '0xa3a1eF5Ae6561572023363862e238aFA84C72ef5',
        'factory' : '',
        'fee': 0
    },
    'dodo' : {
        'pairs' : {
        frozenset(('USDT', 'USDC')) : '0x6790424249cad1bce244b55afbb240703f5265f6',
        frozenset(('NEAR', 'WETH')) : '0xedE8950332E6B618C53E7506bca92012702CA697'
        },
        'router' : '',
        'factory' : '',
        'fee': 0
    }

}
AuroraTestData = {
    'EXCHANGES' : {
    'trisolaris' : {
        'pairs' : {
        frozenset(('AURORA', 'WETH')) : '0x5eeC60F348cB1D661E4A5122CF4638c7DB7A886e',
        frozenset(('NEAR', 'USDT')) : '0x03B666f3488a7992b2385B12dF7f35156d7b29cD',}},
    'auroraswap' : {
        'pairs' : {
        frozenset(('USDT', 'USDC')) : '0xec538fafafcbb625c394c35b11252cef732368cd',
        frozenset(('USDC', 'NEAR')) : '0x480a68ba97d70495e80e11e05d59f6c659749f27',}},
    'wannaswap' : {
        'pairs' : {
        frozenset(('AURORA', 'NEAR')) : '0x7e9ea10e5984a09d19d05f31ca3cb65bb7df359d',
        frozenset(('NEAR', 'WETH')) : '0x256d03607eee0156b8a2ab84da1d5b283219fe97',
        frozenset(('USDC', 'NEAR')) : '0xbf560771b6002a58477efbcdd6774a5a1947587b',}
        }},
    'GRAPH' : {
    'AURORA' : [
        {'to' : 'WETH','via' : 'trisolaris',},
        {'to' : 'NEAR','via' : 'wannaswap',},],
    'WETH' : [
        {'to' : 'AURORA','via' : 'trisolaris',},
        {'to' : 'NEAR','via' : 'wannaswap',},],
    'NEAR' : [
        {'to' : 'USDT','via' : 'trisolaris',},
        {'to' : 'USDC','via' : 'auroraswap',},
        {'to' : 'AURORA','via' : 'wannaswap',},
        {'to' : 'WETH','via' : 'wannaswap',},
        {'to' : 'USDC','via' : 'wannaswap',},],
    'USDC' : [
        {'to' : 'USDT','via' : 'auroraswap',},
        {'to' : 'NEAR','via' : 'auroraswap',},
        {'to' : 'NEAR','via' : 'wannaswap',},],
    'USDT': [
        {'to' : 'NEAR','via' : 'trisolaris',},
        {'to' : 'USDC','via' : 'auroraswap',},],
},
    'TOKENS' : ['AURORA','WETH'],
    'PRICE' : {'WETH': 2.141651224104825, 'WBTC': 0.11160318},
    'ARB_ROUTE' : [
    [
        {
        'from' : 'AURORA',
        'to' : 'WETH',
        'via' : 'trisolaris'},
        {
        'from' : 'WETH',
        'to' : 'NEAR',
        'via' : 'wannaswap'},
        {
        'from' : 'NEAR',
        'to' : 'AURORA',
        'via' : 'wannaswap'},
    ],
    [
        {
        'from' : 'AURORA',
        'to' : 'NEAR',
        'via' : 'wannaswap'},
        {
        'from' : 'NEAR',
        'to' : 'WETH',
        'via' : 'wannaswap'},
        {
        'from' : 'WETH',
        'to' : 'AURORA',
        'via' : 'trisolaris'},
    ],
    [
        {
        'from' : 'WETH',
        'to' : 'AURORA',
        'via' : 'trisolaris'},
        {
        'from' : 'AURORA',
        'to' : 'NEAR',
        'via' : 'wannaswap'},
        {
        'from' : 'NEAR',
        'to' : 'WETH',
        'via' : 'wannaswap'},
    ],
    [
        {
        'from' : 'WETH',
        'to' : 'NEAR',
        'via' : 'wannaswap'},
        {
        'from' : 'NEAR',
        'to' : 'AURORA',
        'via' : 'wannaswap'},
        {
        'from' : 'AURORA',
        'to' : 'WETH',
        'via' : 'trisolaris'},
    ],
    ],
}

# BSC Network

BSCTokens = config["Binance SmartChain"]['Tokens']
BSCStartTokens = ['BSC-USD','WBNB']
BSCStartExchanges = ['pancakeswap', 'sushiswap', 'mdex','biswap','apeswap','babyswap','fstswap']
BSCExchanges = parseEchanges(config["Binance SmartChain"]['Exchanges'])


# Kovan Network
KovanTokens = {

}
KovanStartTokens = {

}
KovanStartExchanges = []
KovanExchanges = {

}

# Arbitrum Network

ArbitrumTokens = {

}
ArbitrumStartTokens = {

}
ArbitrumStartExchanges = []
ArbitrumExchanges = {

}

# Goerli Network

GoerliTokens = {

}

GoerliStartTokens = {

}

GoerliStartExchanges = []

GoerliExchanges = {

}