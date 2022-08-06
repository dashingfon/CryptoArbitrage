# The controller class that prepares and executes arbs

import Config as Cfg
import warnings, json

from eth_abi import encode_abi
#from brownie import config, interface, accounts, BscArb, TestArb
from web3 import Web3
from datetime import datetime, timedelta

class Controller():
    def __init__(self,blockchain):
        self.contract = None
        self.account = None
        self.swapFuncSig = '0x38ed1739' #'swapExactTokensForTokens(uint256,uint256,address[],address,uint256)'
        self.approveFuncSig = '0x095ea7b3' #'approve(address,uint256)'
        self.blockchainMap = Cfg.ControllerBlockchains

        if str(blockchain) in self.blockchainMap:
            self.blockchain = blockchain
        else:
            raise ValueError('Invalid Blockchain Object')
    '''
    def getContract(self):
        if str(self.blockchain) == 'Binance SmartChain':
            if not self.contract:
                self.contract = BscArb[0]
            return self.contract
        elif str(self.blockchain)[-7:] == 'Testnet':
            if not self.contract:
                self.contract = TestArb.deploy({'from' : accounts[0]})
            return self.contract
    
    def getAccount(self):
        if str(self.blockchain) == 'Binance SmartChain':
            if not self.account:
                self.account = accounts.add(config['wallets']['beacon'])
            return self.account
        elif str(self.blockchain)[-7:] == 'Testnet':
            if not self.account:
                self.account = accounts[0]
            return self.account
'''
    def getRoutes(self, pollResult = True, arbRoute = False):
        history = set()

        if pollResult:
            try:
                with open(self.blockchain.pollPath, 'r') as PP:
                    pollPath = json.load(PP)
            except FileNotFoundError:
                warnings.warn('Poll result file not found')
            else:
                for item in pollPath['Data']:
                    route = self.blockchain.assemble(item['route'])
                    routes = self.blockchain.simplyfy(route)
                    history.add(routes[0])
                    history.add(routes[1])
                    if item['EP'] > 0:
                        yield {'route' : routes[2],'simplified' : routes[0],'EP' : item['EP'],'capital' : item['capital']}

        if arbRoute:
            try:
                with open(self.blockchain.routePath, 'r') as PP:
                    routePath = json.load(PP)
            except FileNotFoundError:
                warnings.warn('Route path file not found')
            else:
                for item in routePath['Data']:
                    simplyfiedRoute = self.blockchain.simplyfy(item)
                    if simplyfiedRoute[0] not in history and simplyfiedRoute[1] not in history:
                        history.add(simplyfiedRoute[0])
                        history.add(simplyfiedRoute[1])
                        yield {'route' : simplyfiedRoute[2],'simplified' : simplyfiedRoute[0]}
                
    def check(self, route):
        return self.blockchain.pollRoute(route)

    def getProspect(self,Routes):
        for item in Routes:
            simplyfied = self.blockchain.simplyfy(item['route'])
            if 'EP' in item:
                if item['EP'] > 0:
                    item['EP'] *= 1e18
                    item['capital'] *= 1e18
                    yield item
            elif str(self.blockchain)[-7:] != 'Testnet':
                result = self.check(item['route'])
                
                if result[0][2] > 0:
                    item['EP'] = result[0][2] * 1e18
                    item['capital'] = result[0][0] * 1e18
                    yield item
                elif result[1][2] > 0:
                    item['EP'] = result[1][2] * 1e18
                    item['capital'] = result[1][0] * 1e18
                    item['simplified'] = simplyfied[1]
                    item['route'] = simplyfied[3]
                    yield item
                
    def encodeCall(self,signature,definitions,arguments):
        byteData = encode_abi(definitions,arguments)
        return signature + Web3.toHex(byteData)[2:]

    '''def getAmountsOut(self,router,amount,addresses):
        Router = interface.IRouter(router)
        amounts = Router.getAmountsOut(amount,addresses)
        return amounts[-1]'''


    def sortTokens(self,address1, address2):
        first = str.encode(address1).hex()
        second = str.encode(address2).hex()

        if first > second:
            return (address2,address1)
        elif first < second:
            return (address1,address2)
        else:
            raise ValueError('addresses are the same')

    def getValues(self,item,options):
        '''
        options contents

        * all items are optional

        tokens :- dict
        pair :- address
        fee :- num
        factory :- address
        router :- list
        timeStamp :- bool
        '''
        values = {}

        if 'tokens' in options:
            values['tokens'] = tokens = options['tokens']
        else: 
            values['tokens'] = tokens = self.blockchain.tokens

        values['names'] = names = (item['route'][0]['from'], item['route'][0]['to'])
        token0, token1 = self.sortTokens(tokens[names[0]],tokens[names[1]])
        
        values['amount0'] = int(item['capital']) if tokens[names[0]] == token0 else 0
        values['amount1'] = 0 if tokens[names[1]] == token1 else int(item['capital'])
    
        if 'pair' in options:
            values['pair'] = options['pair']
        else:
            values['pair'] = self.blockchain.exchanges[
            item['route'][0]['via']]['pairs'][frozenset(names[0],names[1])]
        
        if 'factory' in options:
            values['factory']  = options['factory']
        else:
            values['factory'] = self.blockchain.exchanges[item['route'][0]['via']['factory']]
        
        if 'routers' in options:
            assert len(item['route']) == len(options['routers'])
            values['routers'] = options['routers']
        else:
            routers = []
            for i in item['route']:
                routers.append(self.blockchain.exchanges[i['via']]['router'])
            values['routers'] = routers

        if 'fee' in options:
            values['fee'] = options['fee']
        else:
            values['fee'] = self.blockchain.exchanges[item['route'][0]['via']]['fee']

        values['timeStamp'] = options['timeStamp']

        if 'contract' in options:
            values['contract'] = options['contract']

        if 'Outs' in options:
            assert len(item['route']) == len(options['Outs'])
            values['Outs'] = options['Outs']


        return values   

    def prepPayload(self, item, initiator = '0x0000000000000000000000000000000000000000', options = {}):

        val = self.getValues(item = item,options = options)

        tokens = val['tokens']
        AMOUNT0 = val['amount0']
        AMOUNT1 = val['amount1']
        PAIR = val['pair']
        factory = val['factory']
        names = val['names']
        routers = val['routers']


        addresses = []
        data = []

        addr = [tokens[names[0]],tokens[names[1]]]
        amount = int(item['capital'])

        if 'Outs' in val:
            In = int(val['Outs'][0] * amount)
        else:
            In = self.getAmountsOut(routers[0],amount,addr)

        rem = item['route'][1:]
        end = len(rem) - 1

        for index, i in enumerate(rem):
            router = val['routers'][index + 1]
        
            # to populate the addresses list

            if index == 0 or rem[index - 1]['via'] != i['via']:
                addresses.append(tokens[i['from']])
                addr = [tokens[i['from']],tokens[i['to']]]
                addresses.append(router) 
                print(f'addresses snapshot, index {index} :- {addresses}')
            else:
                addr.append(tokens[i['to']])
                

            # to populate the data list

            if index == end or rem[index + 1]['via'] != i['via']:
                # to encode the approve call
                defs = ['address','uint256']
                args = [addresses[-1],In]
                print(f'approve data args, index {index} :- {args}')
                data.append((self.encodeCall(self.approveFuncSig,defs,args)).encode())

                #to encode the swap call
                defs = ['uint256','uint256','address[]','address','uint256']


                if val['timeStamp']:
                    timeStamp = int(datetime.now() + timedelta(minutes = 1).timestamp())
                else:
                    timeStamp = int(9e9)

                if 'Outs' in val:
                    Out = int(val['Outs'][index + 1] * amount)
                else:
                    Out = self.getAmountsOut(router,In,addr)

                if 'contract' in val:
                    contract = val['contract']
                else:
                    contract = self.getContract().address

                args = [In,Out,addr,contract,timeStamp]
                In = Out
                print(f'swap data args, index {index} :- {args}')
                data.append((self.encodeCall(self.swapFuncSig,defs,args)).encode())


        if Out > amount:
            print('payload profitable!')
            print(f'Starting :- {amount}')
            print(f'Ending :- {Out}')
            
            defs = ['address[]','bytes[]','address','address','address','uint256','uint256']
            args = [addresses,data,PAIR,factory,initiator,amount,val['fee']]
            DATA = Web3.toHex(encode_abi(defs,args))

            return [AMOUNT0,AMOUNT1,tokens[val['names'][0]],DATA]
        else:
            print('payload not profitable!')
            return [] 

    def execute(self, payload):
        contract = self.getContract()
        contract.start(*payload,{'from' : self.getAccount()})

    def arb(self, routes = [], amount = 10, keyargs = []):
        
        #keyargs is a list of dictionaries
        if not routes:
            routes = self.getRoutes()
        
        if keyargs:
            assert len(keyargs) == len(routes)

        try:
            for i in range(amount):
                print(f'arbing {i + 1} of {amount} routes')
                prospect = next(self.getProspect(routes))

                if not keyargs:
                    payload = self.prepPayload(prospect) 
                else:
                    payload = self.prepPayload(prospect,keyargs[i])
                
                if payload:    
                    self.execute(payload)

        except StopIteration:
            print('routes exhausted!')


    def scanPair(self):
        #get reserves and compare against balances
        pass
        

    def getSkimProspect(self):
        #scan and yields profitable pairs
        pass


    def storeSkimProspect(self):
        #save the profitable pairs in a json file
        pass


    def skim(self, skims = [], source = ''):
        #Execute the profitable pairs
        
        pass







