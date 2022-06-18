# Aurora Network

AuroraTokenLookup = {

}

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

DodoPools = {
    ('USDT', 'USDC') : '0x6790424249cad1bce244b55afbb240703f5265f6',
    ('NEAR', 'WETH') : '0xedE8950332E6B618C53E7506bca92012702CA697'
}

startTokens = ['USDT', 'USDC', 'NEAR', 'WETH']

Routers = {
    'trisolaris' : '0x2CB45Edb4517d5947aFdE3BEAbF95A582506858B',
    'auroraswap' : '0xA1B1742e9c32C7cAa9726d8204bD5715e3419861',
    'wannaswap' : '0xa3a1eF5Ae6561572023363862e238aFA84C72ef5'
}

AuroraExchanges = {
    'trisolaris' : {
        frozenset(('AURORA', 'WETH')) : '0x5eeC60F348cB1D661E4A5122CF4638c7DB7A886e',
        frozenset(('NEAR', 'WETH')) : '0x63da4DB6Ef4e7C62168aB03982399F9588fCd198',
        frozenset(('NEAR', 'USDC')) : '0x20F8AeFB5697B77E0BB835A8518BE70775cdA1b0',
        frozenset(('NEAR', 'USDT')) : '0x03B666f3488a7992b2385B12dF7f35156d7b29cD',
        frozenset(('USDC', 'USDT')) : '0x2fe064B6c7D274082aa5d2624709bC9AE7D16C77',
        frozenset(('NEAR', 'WBTC')) : '0xbc8A244e8fb683ec1Fd6f88F3cc6E565082174Eb',
        frozenset(('AURORA', 'NEAR')) : '0x1e0e812FBcd3EB75D8562AD6F310Ed94D258D008',
    },

    'auroraswap' : {
        frozenset(('USDT', 'USDC')) : '0xec538fafafcbb625c394c35b11252cef732368cd',
        frozenset(('USDC', 'NEAR')) : '0x480a68ba97d70495e80e11e05d59f6c659749f27',
        frozenset(('USDT', 'NEAR')) : '0xf3de9dc38f62608179c45fe8943a0ca34ba9cefc',
        frozenset(('NEAR', 'WETH')) : '0xc57ecc341ae4df32442cf80f34f41dc1782fe067',
        frozenset(('WETH', 'WBTC')) : '0xcb8584360dc7a4eac4878b48fb857aa794e46fa8'
    },

    'wannaswap' : {
        frozenset(('AURORA', 'NEAR')) : '0x7e9ea10e5984a09d19d05f31ca3cb65bb7df359d',
        frozenset(('NEAR', 'WBTC')) : '0xbf58062d23f869a90c6eb04b9655f0dfca345947',
        frozenset(('NEAR', 'WETH')) : '0x256d03607eee0156b8a2ab84da1d5b283219fe97',
        frozenset(('USDC', 'NEAR')) : '0xbf560771b6002a58477efbcdd6774a5a1947587b',
        frozenset(('USDT', 'NEAR') ): '0x2e02bea8e9118f7d2ccada1d402286cc6d54bd67',
        frozenset(('WETH', 'WBTC')) : '0xf56997948d4235514dcc50fc0ea7c0e110ec255d',
        frozenset(('USDT', 'USDC')) : '0x3502eac6fa27beebdc5cd3615b7cb0784b0ce48f'
    }

}

AuroraParams = {
    'module' : 'account',
    'action' : 'tokenlist',
    'address' : ''
}

AuroraHeaders = {'Host' : 'explorer.mainnet.aurora.dev'}
exampleRequestUrl = 'https://explorer.mainnet.aurora.dev/api?module=account&action=tokenlist&address=0x5eeC60F348cB1D661E4A5122CF4638c7DB7A886e'

# Arbitrum Network