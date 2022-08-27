from copy import copy
from functools import wraps
import time, requests, json
from web3 import Web3
from eth_abi import encode_abi
from bs4 import BeautifulSoup


with open(r'scripts\Config.json') as CJ:
    config = json.load(CJ)

T1, T2 = config['Test']['T1'], config['Test']['T2']
T3, T4 = config['Test']['T3'], config['Test']['T4']
fonswapRouter = config['Test']['fonswapRouter']
dodoRouter = config['Test']['dodoRouter']
PAIR, cap = config['Test']['PAIR'], config['Test']['cap']
fee = config['Test']['fee']

'''
This is the Ratelimited decorator used to limit requests
'''
def RateLimited(maxPerSecond):
    mininterval = 1.0 / float(maxPerSecond)

    def decorate(func):
        lastTimeCalled = [0.0]

        @wraps(func)
        def ratelimitedFunction(*args,**kwargs):
            elapsed = time.process_time_ns() - lastTimeCalled[0]
            lefttowait = mininterval - elapsed
            if lefttowait > 0:
                print(f'waiting {lefttowait} ...')
                time.sleep(lefttowait)
            ret = func(*args, **kwargs)
            lastTimeCalled[0] = time.process_time_ns()
            return ret
        return ratelimitedFunction
    return decorate

def isTestnet(blockchain):
    return str(blockchain)[-7:] == 'Testnet'

def getPaths(contents):
    num = 1
    result = []
    defs = ['address[]']
    for i in contents:
        args = [i]
        result.append(encode_abi(defs,args))
        print(f'address data {num} :- {Web3.toHex(encode_abi(defs,args))}')
    return result

def getPayloadBytes(Map,pair):
    data = getPaths(Map[1])

    defs = ['address[]','bytes[]','address','uint256','uint256']
    args = [Map[0],data,pair,int(cap),fee]
    assert len(args[0]) == len(args[1])

    DATA = Web3.toHex(encode_abi(defs,args))
    print(f'prepped Data :- ')
    print(DATA)
    return DATA

def setPreparedData():
    Map = {
        1 : [[fonswapRouter], [[T2,T3,T1,T4]]],

        2 : [[dodoRouter,fonswapRouter], [[T2,T3,T1],[T1,T4]]],

        3 : [[fonswapRouter,dodoRouter], [[T2,T3],[T3,T1,T4]]],

        4 : [[dodoRouter,fonswapRouter,dodoRouter], [[T2,T3],[T3,T1],[T1,T4]]]
    }
    result = []
    for i in range(1,5):
        result.append(getPayloadBytes(Map[i]))
    config['Test']['PrepedSwapData'] = result
    with open(r'scripts\Config.json','w') as CJ:
        json.dump(config,CJ,indent = 2)

def poll(chain,route,prices):
    print(chain.pollRoute(route = route, prices = prices))

def sortTokens(address1, address2):
    first = str.encode(address1).hex()
    second = str.encode(address2).hex()

    if first > second:
        return (address2,address1)
    elif first < second:
        return (address1,address2)
    else:
        raise ValueError('addresses are the same')




def extractSymbol(content):
    print('extracting symbol ...')
    try:
        soup = BeautifulSoup(content, 'html.parser')
        placeHolder = soup.find('div',id = "ContentPlaceHolder1_tr_tokeninfo")
        #print(placeHolder)
        raw = placeHolder.find('a').string.split()[-1]
    except Exception as e:
        print('an error occured')
        print(e)
        return ''
    print('extracted')
    return raw[1:-1]

@RateLimited(2)
def fetch(url,session,headers,params):
    print('fetching data ...')
    attemptsAllowed = 4
    tries = 0
    done = False

    while tries < attemptsAllowed and not done:
        try:
            response = session.get(url,headers = headers,params = params)
        except ConnectionError:
            print('Error')
            time.sleep(10)
            tries += 1
            print(f'Retring... \n{attemptsAllowed - tries} tries left')
        else:
            done = True

    if response.status_code == 200:
        return response
    else:
        print('unsuccesful request!')
        print(f'status code :- {response.status_code}')
        return {}

def cache(content,name):
    print('caching content ...')
    tokens = {}
    exchanges = {}

    for i in content['included']:
        if i['type'] == 'dex':
            exchanges[i['id']] = i['attributes']['identifier']
        elif i['type'] == 'token' :
            tokens[i['id']] = {'symbol': i['attributes']['symbol'],
                            'address' : i['attributes']['address']}
        elif i['type'] == 'network':
            assert i['attributes']['identifier'] == name

    return (tokens,exchanges)

def trim_and_map(blockchain, tokens, exchanges):
    print('trimming and mapping ...')
    tokensResult = {}
    exchangesResult = {}
    remappingsResult = {}
    checked = set()

    blockchain.tokens = tokens
    blockchain.exchanges = exchanges

    initialExchangeCount = 0
    for val in exchanges.values():
        for v in val['pairs'].values():
            initialExchangeCount += len(v)

    routes = blockchain.getArbRoute(tokens = 'all',save = False)

    print(f'total routes / {len(routes) - 1}')
    session = requests.Session()

    for item in routes:
        for swap in item:
            to, fro, via = swap['to'], swap['from'], swap['via']
            if to not in checked:
                checked.add(to)
                toAddress = tokens[to]
                toResponse = fetch(
                    blockchain.source + toAddress,session,blockchain.headers,{})
                assert toResponse, "Got an empty response..."
                toSymbol = extractSymbol(toResponse.text)
                assert toSymbol, 'Empty to Symbol'
                if to != toSymbol:
                    remappingsResult[to] = toSymbol
                tokensResult[toSymbol] = toAddress
            elif to in remappingsResult:
                    toSymbol = remappingsResult[to]
            else:
                toSymbol = to

            if fro not in checked:
                checked.add(fro)
                fromAddress = tokens[fro]
                fromResponse = fetch(
                    blockchain.source + fromAddress,session,blockchain.headers,{})
                assert fromResponse, "Got an empty response..."
                fromSymbol = extractSymbol(fromResponse.text)
                assert fromSymbol, 'Empty from symbol'
                if fro != fromSymbol:
                    remappingsResult[fro] = fromSymbol
                tokensResult[fromSymbol] = fromAddress
            elif fro in remappingsResult:
                    toSymbol = remappingsResult[fro]
            else:
                toSymbol = fro 

            if via not in exchangesResult:
                exchangesResult[via] = copy(exchanges[via])
                exchangesResult[via]['pairs'] = {}

            exchangesResult[via]['pairs'][frozenset(
                (toSymbol,fromSymbol))] = exchanges[via]['pairs'][frozenset((fro,to))]
    
    finalExchangeCount = 0
    for val in exchangesResult.values():
        for v in val['pairs'].values():
            finalExchangeCount += len(v)

    return {
        'MetaData' : {
            'initialTokenCount' : len(tokens),
            'initialPairsCount' : initialExchangeCount,
            'finalTokenCount' : len(tokensResult),
            'finalTokenCount' : finalExchangeCount
        },
        'Data': {
            "TokensRemappings": remappingsResult, 
            "Tokens": tokensResult, 
            "Exchanges": exchangesResult  }
        }

def buildData(blockchain,minLiquidity = 150000):
    print('building Data ...')
    tokens, exchanges = {}, {}
    filePath = 'dataDump.json'
    url = f'https://app.geckoterminal.com/api/p1/{blockchain.geckoTerminalName}/pools'
    headers = copy(blockchain.headers)
    headers['Host'] = 'app.geckoterminal.com'
    params = {
        'include' : 'dex%2Cdex.network%2Cdex.network.network_metric%2Ctokens',
        'page' : 1,
        'items' : 100
    }
    session = requests.Session()

    Done = False
    while not Done:
        print(f"Page {params['page']} ...")
        raw = fetch(url,session,headers,params)
        assert raw,"Fetched Data is empty..."
        data = raw.json()
        tokenCache, exchangeCache = cache(data,blockchain.geckoTerminalName)

        for item in data['data']:
            assert item['type'] == 'pool'
            if item['attributes']['reserve_in_usd'] >= minLiquidity:
                Ts = []
                rel = item['relationships']
                for i in rel['tokens']['data']:
                    assert i['type'] == 'token'
                    tokens[tokenCache[i['id']]['symbol']] = tokenCache[i['id']]['address']
                    Ts.append(tokenCache[i['id']]['symbol'])

                dex = rel['dex']['data']['id']
                if exchangeCache[dex] not in exchanges:
                    exchanges[exchangeCache[dex]] = {
                        'pairs': {},
                        'router' : '',
                        'factory' : ''
                    }
                exchanges[exchangeCache[dex]]['pairs'][frozenset(Ts)] = item['attributes']['address']
                
        if data['links']['next']:
            params['page'] += 1
        else: 
            Done = True
            print('Done')

    result = trim_and_map(blockchain,tokens,exchanges)
    dump = {
        "MetaData" : {
            'datetime' : time.ctime(),**result['MetaData']
        },
        "Data" : result['Data'],
        'Raw' : {
            'Tokens' : tokens,
            'Exchanges' : exchanges
        }
    }
    with open(filePath,'w') as FP:
        json.dump(dump,FP,indent = 2)

if __name__ == '__main__':
    pass




