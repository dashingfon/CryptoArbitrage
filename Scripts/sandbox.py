import scripts.Blockchains as Blc
import scripts.utills as utills
import time, requests, asyncio, aiohttp
from bs4 import BeautifulSoup
import scripts.Config as Cfg
import datetime
#from brownie import interface


route = [
    {"from" : "TST4","to" : "TST2","via" : "fonswap"},
    {"from" : "TST2","to" : "TST3","via" : "fonswap"},
    {"from" : "TST3","to" : "TST1","via" : "fonswap"},
    {"from" : "TST1","to" : "TST4","via" : "fonswap"}
]
prices = [
    {'TST4' : 60, 'TST2' : 80},
    {'TST2' : 70, 'TST3' : 65},
    {'TST3' : 50, 'TST1' : 67},
    {'TST1' : 47, 'TST4' : 67}
]

config = utills.config

def pullDataFromDump(chain,exchanges,temp = False):
    path = r'data\dataDump.json'
    utills.setExchangesData(chain,path,exchanges,temp)

def findSymbol(symbol):
    tokens = utills.readJson(r'data\artifactDump.json')['tokens']
    print(tokens[symbol])

def testParser():
    html = """<div id="ContentPlaceHolder1_tr_tokeninfo">
<hr/>
<div class="row align-items-center">
<div class="col-md-4 mb-1 mb-md-0">
<span class="d-md-none d-lg-inline-block mr-1">Token</span>Tracker:</div>
<div class="col-md-8">
<img src="/token/images/axieinfinity_32.png" style="margin-left: -5px" width="20"/> <a data-toggle="tooltip" href="/token/0x715d400f88c167884bbcc41c5fea407ed4d2f8a0" title="View Token Tracker Page"><span>Binance-Peg Axie Infinity Shard To...</span> (AXS)</a> <span class="text-secondary">(@$13.88)</span></div>
</div>
</div>"""

    sec = '<a href="/token/0xce4a4a15fccd532ead67be3ecf7e6122c61d06bb" data-toggle="tooltip" title="" data-original-title="View 0xce4a4a15fccd532ead67be3ecf7e6122c...  Token Tracker Page">ThunderCake (<span>THUNDERCA...</span>)</a>'
    
    soup = BeautifulSoup(sec,'html.parser')
    raw = soup.find('a').contents[-1].split('(')[-1].split(')')[0]
    #raw = soup.find('a').contents[-1].split()[-1]
    print(raw)

def pull():
    chain = Blc.BSC()
    tokens = utills.readJson(r'data\artifactDump.json')['tokens']
    exchanges = utills.readJson(r'data\artifactDump.json')['exchanges']
    trimmed = utills.trim_and_map(chain,tokens,exchanges)
    trimmed['MetaData']['datetime'] = time.ctime()
    utills.writeJson(r'data\dataDump.json',trimmed)

def main():
    chain = Blc.Aurora()
    utills.buildData(chain, minLiquidity = 75000, saveArtifact = True)
    #pullDataFromDump(chain,Cfg.AuroraExchanges,True)




if __name__ == '__main__': 
    #main()
    chain = Blc.Aurora()

    async def test():
        async with aiohttp.ClientSession() as sess:
            addr = "0x16b9a82891338f9ba80e2d6970fdda79d1eb0dae"
            async with await chain.fetch(sess,addr) as resp:
                print(resp.status)
                print(await resp.text())
    
    asyncio.get_event_loop().run_until_complete(test())

    

