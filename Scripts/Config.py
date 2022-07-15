 
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
        'library' : '',
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
        'library' : '',
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
        'library' : '',
    },
    'dodo' : {
        'pairs' : {
        frozenset(('USDT', 'USDC')) : '0x6790424249cad1bce244b55afbb240703f5265f6',
        frozenset(('NEAR', 'WETH')) : '0xedE8950332E6B618C53E7506bca92012702CA697'
        },
        'router' : '',
        'library' : '',
    }

}

# BSC Network

# USDT is BSC-USD
BSCTokens = {
    'WBNB' : '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c',
    'BUSD' : '0xe9e7cea3dedca5984780bafc599bd69add087d56',
    'BSC-USD' : '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d',
    'USDT' : '0xe9e7cea3dedca5984780bafc599bd69add087d56',
    'ETH' : '0x2170ed0880ac9a755fd29b2688956bd959f933f8',
    'BTCB' : '0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c',
}
# notable mentions, frax, ada, link, sushi

BSCStartTokens = ['USDC']

BSCStartExchanges = ['pancakeswap', 'sushiswap', 'dodo','biswap','apeswap','bakeryswap']

BSCExchanges = {
    'pancakeswap' : {
        'pairs' : {
        frozenset(('BSC-USD','BUSD')) : '0x7efaef62fddcca950418312c6c91aef321375a00',
        frozenset(('WBNB','BUSD')) : '0x58f876857a02d6762e0101bb5c46a8c1ed44dc16',
        frozenset(('BSC-USD','WBNB')) : '0x16b9a82891338f9ba80e2d6970fdda79d1eb0dae',
        frozenset(('USDC','BUSD')) : '0x2354ef4df11afacb85a5c7f98b624072eccddbb1',
        frozenset(('BSC-USD','USDC')) : '0xec6557348085aa57c72514d67070dc863c0a5a8c',
        frozenset(('BTCB','BUSD')) : '0xf45cd219aef8618a92baa7ad848364a158a24f33',
        frozenset(('BTCB','WBNB')) : '0x61eb789d75a95caa3ff50ed7e47b96c132fec082',
        frozenset(('ETH','WBNB')) : '0x74e4716e431f45807dcf19f284c7aa99f18a4fbc',
        frozenset(('ETH','BTCB')) : '0xd171b26e4484402de70e3ea256be5a2630d7e88d',
        frozenset(('USDC','WBNB')) : '0xd99c7f6c65857ac913a8f880a4cb84032ab2fc5b',
        },
        'router' : '',
        'library' : '',
    },
    'biswap' : {
        'pairs' : {
        frozenset(('BSC-USD','BUSD')) : '0xda8ceb724a06819c0a5cdb4304ea0cb27f8304cf',
        frozenset(('WBNB','BUSD')) : '0xacaac9311b0096e04dfe96b6d87dec867d3883dc',
        frozenset(('BSC-USD','WBNB')) : '0x8840c6252e2e86e545defb6da98b2a0e26d8c1ba',
        frozenset(('ETH','WBNB')) : '0x5bf6941f029424674bb93a43b79fc46bf4a67c21',
        frozenset(('BTCB','WBNB')) : '0xc7e9d76ba11099af3f330ff829c5f442d571e057',
        frozenset(('BSC-USD','USDC')) : '0x1483767e665b3591677fd49f724bf7430c18bf83',
        frozenset(('BSC-USD','BTCB')) : '0x1483767e665b3591677fd49f724bf7430c18bf83',
        frozenset(('ETH','BSC-USD')) : '0x63b30de1a998e9e64fd58a21f68d323b9bcd8f85',
        frozenset(('ETH','BTCB')) : '0x6216e04cd40db2c6fbed64f1b5830a98d3a91740',
        frozenset(('USDC','WBNB')) : '0x06cd679121ec37b0a2fd673d4976b09d81791856',
        },
        'router' : '',
        'library' : '',
    },
    'dodo' : {
        'pairs' : {
        frozenset(('BUSD','BSC-USD')) : '0xbe60d4c4250438344bec816ec2dec99925deb4c7',
        frozenset(('USDC','BUSD')) : '0x6064dbd0ff10bfed5a797807042e9f63f18cfe10',
        },
        'router' : '',
        'library' : '',
    },
    'sushiswap' : {
        'pairs' : {
        frozenset(('BSC-USD','WBNB')) : '0x2905817b020fd35d9d09672946362b62766f0d69',
        frozenset(('WBNB','BUSD')) : '0xdc558d64c29721d74c4456cfb4363a6e6660a9bb',
        frozenset(('USDC','WBNB')) : '0xc7632b7b2d768bbb30a404e13e1de48d1439ec21',
        frozenset(('ETH','WBNB')) : '0x6da1ffd9d24e1753d2f46ca53146116c7210b3c5',
        frozenset(('ETH','BTCB')) : '0xc06949431e4e88cb50ad4df176dc409ab1c78fe2',
        },
        'router' : '',
        'library' : '',
    },
    'mdex' : {
        'pairs' : {
        frozenset(('BSC-USD','BUSD')) : '0x62c1dec1ff328dcdc157ae0068bb21af3967acd9',
        frozenset(('BSC-USD','WBNB')) : '0x09cb618bf5ef305fadfd2c8fc0c26eecf8c6d5fd',
        frozenset(('BSC-USD','USDC')) : '0x9f4da89774570e27170873befd139a79cb1a3da2',
        frozenset(('ETH','BSC-USD')) : '0x0fb881c078434b1c0e4d0b64d8c64d12078b7ce2',
        frozenset(('BSC-USD','BTCB')) : '0xda28eb7aba389c1ea226a420bce04cb565aafb85',
        frozenset(('ETH','BTCB')) : '0x577d005912c49b1679b4c21e334fdb650e92c077',
        frozenset(('ETH','WBNB')) : '0x82e8f9e7624fa038dff4a39960f5197a43fa76aa',
        frozenset(('WBNB','BUSD')) : '0x340192d37d95fb609874b1db6145ed26d1e47744',
        frozenset(('BTCB','WBNB')) : '0x969f2556f786a576f32aef6c1d6618f0221ec70e',
        },
        'router' : '',
        'library' : '',
    },
    'apeswap' : {
       'pairs' : {
        frozenset(('USDC','BUSD')) : '0xc087c78abac4a0e900a327444193dbf9ba69058e',
        frozenset(('BSC-USD','BUSD')) : '0x2e707261d086687470b515b320478eb1c88d49bb',
        frozenset(('WBNB','BUSD')) : '0x51e6d27fa57373d8d4c256231241053a70cb1d93',
        frozenset(('ETH','WBNB')) : '0xa0c3ef24414ed9c9b456740128d8e63d016a9e11',
        frozenset(('BTCB','WBNB')) : '0x1e1afe9d9c5f290d8f6996ddb190bd111908a43d',
        frozenset(('BSC-USD','WBNB')) : '0x83c5b5b309ee8e232fe9db217d394e262a71bcc0',
        },
        'router' : '',
        'library' : '',
    },
    'bakeryswap' : {
       'pairs' : {
        frozenset(('WBNB','BUSD')) : '0x559e3d9611e9cb8a77c11335bdac49621382188b',
        frozenset(('BTCB','WBNB')) : '0x58521373474810915b02fe968d1bcbe35fc61e09',
        frozenset(('BSC-USD','WBNB')) : '0x9ec271c041a18aa7bef070a1f196eea1d06ab7cb',
        frozenset(('USDC','BUSD')) : '0x56cde265aad310e623c8f8994a5143582659abfc',
        frozenset(('BSC-USD','BUSD')) : '0xbcf3278098417e23d941613ce36a7ce9428724a5',
       },
       'router' : '',
        'library' : '',
    },
    'babyswap' : {
         'pairs' :{
        frozenset(('BSC-USD','BUSD')) : '0x249cd054697f41d73f1a81fa0f5279fcce3cf70c',
        frozenset(('BSC-USD','WBNB')) : '0x04580ce6dee076354e96fed53cb839de9efb5f3f',
        frozenset(('BSC-USD','USDC')) : '0xcc21b0a9a01fcd2103ff75614480bd6a07869053',
        frozenset(('WBNB','BUSD')) : '0xdf84c66e5c1e01dc9cbcbbb09f4ce2a1de6641d6',
        frozenset(('USDC','WBNB')) : '0xbf83ca11abc62447226f6b3566918d3594ba3803',
        },
        'router' : '',
        'library' : '',
    },
}


# Arbitrum Network

ArbitrumTokens = {

}

ArbitrumStartTokens = {

}

ArbitrumRouters = {

}

ArbitrumExchanges = {

}
