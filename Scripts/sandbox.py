import scripts.Blockchains as Blc
import scripts.utills as utills
import time, asyncio, aiohttp
from bs4 import BeautifulSoup
import scripts.Config as Cfg
import datetime, os
from cache import AsyncTTL
from asyncio.proactor_events import _ProactorBasePipeTransport
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
    _ProactorBasePipeTransport.__del__ = utills.silence_event_loop_closed(_ProactorBasePipeTransport.__del__)

    chain = Blc.BSC()

    async def test(addr,content,sess):
        '''async with await chain.fetch(sess,addr) as resp:
            print(resp.status)
            print(chain.extract(await resp.text(),content))
'''     
        return await chain.getPrice(sess,addr,content,'testing')
        

    async def main(addrs,conts):
        assert len(addrs) == len(conts)
        async with aiohttp.ClientSession() as sess:
            tasks = [test(addr,swap,sess) for addr, swap in zip(addrs,conts)]
            await asyncio.gather(*tasks)


    addr1 = "0xd171b26e4484402de70e3ea256be5a2630d7e88d"
    cont1 = {'from' : 'BTCB_e3ead9c', 'to' : 'ETH_9f933f8'}
    
    
    addr2 = "0x5292600758a090490d34367d4864ed6291d254fe"
    cont2 = {'from': "BUSD_d087d56", 'to': "FRAX_3e89f40"}
    
    #asyncio.new_event_loop().run_until_complete(test(addr1,cont1),test(addr2,cont2))
    #asyncio.new_event_loop().run_until_complete(test(addr1,cont1))

    
    #asyncio.run(main([addr1,addr2],[cont1,cont2]),debug=True)
    
    @AsyncTTL(time_to_live = 5, maxsize = 200)
    async def test():
        print('fetching')
        return 3

    async def postTest():
        tasks = [asyncio.create_task(test())] * 3
        return await asyncio.gather(*tasks)


    async def tester():
        tasks = [asyncio.create_task(postTest())] * 3
        res = await asyncio.gather(*tasks)
        print(*res)

    asyncio.run(tester())

    def evalExchanges(batch):
        routes = utills.readJson(chain.routePath)['Data']
        distribution = {}
        exchanges = chain.exchanges
        batches = utills.split_list(routes, batch)
        print(f'lenght of routes :- {len(routes)}')
        lenght = 0

        for item in batches:
            store = set()
            for route in item:
                for swap in route:
                    store.add(exchanges[swap['via']]['pairs']
                        [frozenset([swap['from'],swap['to']])])
            if len(store) not in distribution:
                distribution[len(store)] = 0
            distribution[len(store)] += 1
            lenght += 1

        print(f'lenght of batches :- {lenght}')
        print(distribution)

    evalExchanges(30)

