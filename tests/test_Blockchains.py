import scripts.Blockchains as Blc
from scripts.Utills import readJson
from scripts import CONFIG_PATH
import pytest

Data_Available = 0
Config = readJson(CONFIG_PATH)

EXCHANGES = {
    "trisolaris": {
        "pairs": {
            "AURORA_3bc095c - WETH_3bc095c":
                "0x5eeC60F348cB1D661E4A5122CF4638c7DB7A886e",
            "NEAR_3bc095c - USDT_3bc095c":
                "0x03B666f3488a7992b2385B12dF7f35156d7b29cD"
            },
        'fee': 94550,
        'router': '0x03B666f3488a7992b2385B12dF7f35156d7b29cD'

    },
    "auroraswap": {
        "pairs": {
            "USDT_3bc095c - USDC_3bc095c":
                "0xec538fafafcbb625c394c35b11252cef732368cd",
            "USDC_3bc095c - NEAR_3bc095c":
                "0x480a68ba97d70495e80e11e05d59f6c659749f27"
            },
        'fee': 94550,
        'router': '0x03B666f3488a7992b2385B12dF7f35156d7b29cD'
    },
    "wannaswap": {
        "pairs": {
            "AURORA_3bc095c - NEAR_3bc095c":
                "0x7e9ea10e5984a09d19d05f31ca3cb65bb7df359d",
            "NEAR_3bc095c - WETH_3bc095c":
                "0x256d03607eee0156b8a2ab84da1d5b283219fe97",
            "USDC_3bc095c - NEAR_3bc095c":
                "0xbf560771b6002a58477efbcdd6774a5a1947587b"
            },
        'fee': 94550,
        'router': '0x03B666f3488a7992b2385B12dF7f35156d7b29cD'
    }
    }

TOKENS = {
    'AURORA_3bc095c': "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
    'WETH_3bc095c': "0xcb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
    'USDC_3bc095c': "0xeb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
    'NEAR_3bc095c': "0xfb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
    'USDT_3bc095c': "0x1b4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
}


@pytest.fixture(scope='module')
def ChainSetup():
    Chain = Blc.Test()
    Chain.buildGraph(EXCHANGES)
    return Chain


@pytest.fixture(scope='module')
def ChainGraph(ChainSetup):
    return ChainSetup.graph


@pytest.fixture(scope='module')
def ChainExchanges(ChainSetup):
    return ChainSetup.exchanges


def test_BuildGraph(ChainGraph):
    for key, value in ChainGraph.items():
        for item in value:
            assert {'to': key, 'via': item['via']} in ChainGraph[item['to']]


class TestArbRoute:

    def test_dive(self, ChainSetup):
        pass

    def test_DLS(self, ChainSetup):

        route = ChainSetup.DLS('AURORA', EXCHANGES)
        route2 = ChainSetup.DLS('WETH', )
        assert equal(route, ARB_ROUTE[:2])
        assert equal(route2, ARB_ROUTE[2:])

    def complete(self, chain, routes):
        for i in routes:
            if chain.simplyfy(i)[3] not in routes:
                return False
        return True

    # testing default as token
    def test_normalGetRoute(self, ChainSetup):
        route = ChainSetup.getArbRoute(tokens=TOKENS, save=False,
                                       exchanges='all', graph=False,
                                       screen=False)
        print(route)
        assert unique(route)
        assert self.complete(ChainSetup, route)


def test_screenRoute(ChainSetup):
    pass
