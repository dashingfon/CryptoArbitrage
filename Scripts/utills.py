from functools import wraps, lru_cache
from datetime import timedelta, datetime
import time, requests, json, os
from web3 import Web3
from eth_abi import encode_abi
from bs4 import BeautifulSoup



def readJson(path):
    try:
        with open(path) as PP:
            temp = json.load(PP)
    except FileNotFoundError as e:
        print(e)
        temp = {}
    return temp

def writeJson(path,content):
    with open(path,'w') as PP:
        json.dump(content, PP, indent = 2)

ConfigPath = r'scripts\Config.json'
config = readJson(ConfigPath)

T1, T2 = config['Test']['T1'], config['Test']['T2']
T3, T4 = config['Test']['T3'], config['Test']['T4']
fonswapRouter = config['Test']['fonswapRouter']
dodoRouter = config['Test']['dodoRouter']
PAIR, cap = config['Test']['PAIR'], config['Test']['cap']
fee = config['Test']['fee']

'''
This is the Ratelimited decorator used to limit requests
'''
def split_list(listA: list[dict[str, str]], n: int):
    for x in range(0, len(listA), n):
        chunk = listA[x: n + x]
        yield chunk

def silence_event_loop_closed(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except RuntimeError as e:
            if str(e) != 'Event loop is closed':
                raise
    return wrapper


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

def lookupPrice(Chain):
    lookup = Chain.lookupPrice(returns = True)
    tokens = Chain.tokens
    for key, value in tokens.items():
        if value not in lookup:
            print(f'Token {key}, Address {value} not included')

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

def extractSymbol(content):
    print('extracting symbol ...')
    try:
        soup = BeautifulSoup(content, 'html.parser')
        placeHolder = soup.find('div',id = "ContentPlaceHolder1_tr_tokeninfo")
        #print(placeHolder)
        raw = placeHolder.find('a').contents[-1].split('(')[-1].split(')')[0]
    except Exception as e:
        print('an error occured')
        print(placeHolder)
        print(e)
        return None
    return raw

@RateLimited(2)
def fetch(url,session,Headers,Params):
    print('fetching data ...')
    attemptsAllowed = 4
    tries = 0
    done = False

    while tries < attemptsAllowed and not done:
        try:
            response = session.get(url = url,headers = Headers,params = Params)
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

def trim_and_map(blockchain, tokens, exchanges, minSwaps = 3):
    print('trimming and mapping ...')
    exchanges = parseEchanges(exchanges)
    assert exchanges
    tokensResult, exchangesResult, remappingsResult = {}, {}, {}
    swapsCount, distribution = 0, {}
    checked, ignore = set(), set()

    initialTokens = len(tokens)
    initialExchangeCount = 0
    for val in exchanges.values():
        initialExchangeCount += len(val['pairs'])

    print(f'Total initial tokens :- {initialTokens}')
    print(f'Total initial exchanges :- {initialExchangeCount}')

    session = requests.Session()
    blockchain.buildGraph(exchanges)

    for token, swaps in blockchain.graph.items():
        swapLenght = len(swaps)
        if swapLenght not in distribution:
            distribution[swapLenght] = 0
        distribution[swapLenght] += 1
        swapsCount += swapLenght

        if swapLenght < minSwaps:
            ignore.add(token)
            continue
        elif token not in checked and token not in ignore:
            address = tokens[token]
            froResponse = fetch(
                    blockchain.source + address,session,blockchain.headers,{})
            assert froResponse, "Empty response returned"
            froSymbol = extractSymbol(froResponse.text)
            if not froSymbol: 
                ignore.add(token)
                continue
            froSymbol = f'{froSymbol}_{address[-7:]}'
            tokensResult[froSymbol] = address
            if token != froSymbol:
                remappingsResult[token] = froSymbol
            checked.add(token)

    for via, val in exchanges.items():
        for key, value in val['pairs'].items():
            tokens = list(key)
            if tokens[0] in ignore or tokens[1] in ignore:
                continue
            token0 = tokens[0] if tokens[0] not in remappingsResult else remappingsResult[tokens[0]]
            token1 = tokens[1] if tokens[1] not in remappingsResult else remappingsResult[tokens[1]]

            if via not in exchangesResult:
                exchangesResult[via] = {'pairs' : {},'router' : '','factory' : ''}
            exchangesResult[via]['pairs'][f'{token0} - {token1}'] = value

    finalExchangeCount = 0
    for val in exchangesResult.values():
        finalExchangeCount += len(val['pairs'])

    return {
        'MetaData' : {
            'TokenCount' : {
                'initial' : initialTokens,
                'final' : len(tokensResult)
            },
            'PairsCount' : {
                'initial' : initialExchangeCount,
                'final' : finalExchangeCount
            },
            'SwapsPerToken' : swapsCount/initialTokens,
            'Distribution' : distribution
        },
        'Data': {
            "TokensRemappings": remappingsResult, 
            "Tokens": tokensResult, 
            "Exchanges": exchangesResult }
        }

def buildData(blockchain, minLiquidity = 300000, saveArtifact = False):
    print(f'building {str(blockchain)} Data ...\n')
    tokens, exchanges = {}, {}
    filePath = os.path.join(blockchain.dataPath,'dataDump.json')
    artifactPath = os.path.join(blockchain.dataPath,'artifactDump.json')
    url = f'https://app.geckoterminal.com/api/p1/{blockchain.geckoTerminalName}/pools?include=dex%2Cdex.network%2Cdex.network.network_metric%2Ctokens&page=1&items=100'
    page = 1
    session= requests.Session()

    Done = False
    while not Done:
        print(f"Page {page} ...")
        raw = fetch(url,session,{},{})
        assert raw,"Fetched Data is empty..."
        data = raw.json()
        tokenCache, exchangeCache = cache(data,blockchain.geckoTerminalName)

        for item in data['data']:
            assert item['type'] == 'pool'
            if float(item['attributes']['reserve_in_usd']) >= minLiquidity:
                Ts = []
                rel = item['relationships']
                for i in rel['tokens']['data']:
                    assert i['type'] == 'token'
                    symbol = f"{tokenCache[i['id']]['symbol']}_{tokenCache[i['id']]['address'][-7:]}"
                    tokens[symbol] = tokenCache[i['id']]['address']
                    Ts.append(symbol)

                dex = rel['dex']['data']['id']
                if exchangeCache[dex] not in exchanges:
                    exchanges[exchangeCache[dex]] = {
                        'pairs': {},
                        'router' : '',
                        'factory' : ''
                    }
                exchanges[exchangeCache[dex]]['pairs'][' - '.join(Ts)] = item['attributes']['address']
                
        if data['links']['next']:
            url = data['links']['next']
            page += 1
        else: 
            Done = True
            print('Done')

    if saveArtifact:
        writeJson(artifactPath,{
            "MetaData" : {
            'datetime' : time.ctime(),
            'blockchain' : str(blockchain),
        },
        "Data" : {'tokens' : tokens,
            'exchanges' : exchanges},
            
        })

    result = trim_and_map(blockchain,tokens,exchanges)

    writeJson(filePath,{
        "MetaData" : {
            'datetime' : time.ctime(),
            'blockchain' : str(blockchain),
            'minimunLiquidity' : minLiquidity,
            **result['MetaData']
        },
        "Data" : result['Data'],
        })

def setExchangesData(chain,dumpPath,existingExchange,temp = True):
    dump = readJson(dumpPath)['Data']
    result = {}
    for key in dump['Exchanges'].keys():
        if key in existingExchange:
            result[key] = existingExchange[key]
            result[key]['pairs'] = dump['Exchanges'][key]['pairs']
        else:
            result[key] = dump['Exchanges'][key]
    
    dump['Exchanges'] = result
    config[str(chain)] = dump

    Path = ConfigPath if not temp else r'temp.json'
    writeJson(Path,config)



