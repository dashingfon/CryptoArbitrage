# The controller class that prepares and executes arbs
import os
import Config as Cfg
import warnings, json

from eth_abi import encode_abi
from web3 import Web3


class Controller():
    def __init__(self,blockchain):
        self.contractAbi = Cfg.contractAbi
        self.contractAddress = None
        self.routerAbi = Cfg.routerAbi
        self.swapFuncSig = '0x38ed1739' #'swapExactTokensForTokens(uint256,uint256,address[],address,uint256)'
        self.approveFuncSig = '0x095ea7b3' #'approve(address,uint256)'
        self.blockchainMap = Cfg.ControllerBlockchains
        self.optimalAmount = 1.009027027
        if str(blockchain) in self.blockchainMap:
            self.blockchain = blockchain
        else:
            raise ValueError('Invalid Blockchain Object')
        self.web3 = Web3(Web3.HTTPProvider(self.blockchain.url,request_kwargs={'timeout':300}))
        self.pv = os.environ.get('BEACON')

    
    def isTestnet(self):
        return str(self.blockchain)[-7:] == 'Testnet'

    def getContract(self,address = '',abi = ''):
        if not address:
            address = self.contractAddress
        if not abi:
            abi = self.contractAbi
        return self.web3.eth.contract(address = address, abi = abi)

    def getAccount(self):
        if self.isTestnet():
            return self.web3.eth.accounts[0]
        else:
            return self.web3.eth.account.from_key(self.pv)

    def getRoutes(self, pollResult = True, arbRoute = False):
        history = set()

        if arbRoute:
            self.blockchain.pollRoutes()
            pollResult = True

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
         
    def check(self, route):
        return self.blockchain.pollRoute(route)

    def getProspect(self,Routes):
        for item in Routes:
            simplyfied = self.blockchain.simplyfy(item['route'])
            if 'EP' in item and item['EP']/item['capital'] >= self.optimalAmount:
                item['EP'] *= 1e18
                item['capital'] *= 1e18
                item['simplified'] = simplyfied[0]
                item['route'] = simplyfied[2]
                yield item
            elif 'EP' not in item and str(self.blockchain)[-7:] != 'Testnet':
                result = self.check(item['route'])
                
                if result[0][2] / result[0][0] >= self.optimalAmount:
                    item['EP'] = result[0][2] * 1e18
                    item['capital'] = result[0][0] * 1e18
                    item['simplified'] = simplyfied[0]
                    yield item
                elif result[1][2] / result[1][0] >= self.optimalAmount:
                    item['EP'] = result[1][2] * 1e18
                    item['capital'] = result[1][0] * 1e18
                    item['simplified'] = simplyfied[1]
                    item['route'] = simplyfied[3]
                    yield item
    
    @staticmethod
    def encodeCall(signature,definitions,arguments):
        byteData = encode_abi(definitions,arguments)
        return signature + Web3.toHex(byteData)[2:]

    def getAmountsOut(self,routerAddress,amount,addresses):
        Router = self.getContract(routerAddress,self.routerAbi)
        amounts = Router.functions.getAmountsOut(amount,addresses).call()
        return amounts[-1]

    @staticmethod
    def sortTokens(address1, address2):
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
        factory :- address
        router :- list
        '''
        values = {}

        if 'tokens' in options:
            values['tokens'] = options['tokens']
        else: 
            values['tokens'] = self.blockchain.tokens

        values['names'] = names = (item['route'][0]['from'], item['route'][0]['to'])
        
        if 'routers' in options:
            assert len(item['route']) == len(options['routers'])
            values['routers'] = options['routers']
        else:
            routers = []
            for i in item['route']:
                routers.append(self.blockchain.exchanges[i['via']]['router'])
            values['routers'] = routers

        if 'pair' in options:
            values['pair'] = options['pair']
        else:
            values['pair'] = self.blockchain.exchanges[
            item['route'][0]['via']]['pairs'][frozenset(names[0],names[1])]
        
        if 'factory' in options:
            values['factory']  = options['factory']
        
        if 'fee' in options:
            values['fee'] = options['fee']

        return values   

    def prepPayload(self, item, options = {}):

        val = self.getValues(item = item,options = options)

        tokens, amount = val['tokens'], int(item['capital'])
        addresses, data = [], []

        if 'fee' in val:
            fee = val['fee']
        else: fee = self.blockchain.exchanges[item['route'][0]['via']]['fee']

        isOut = True
        if 'out' not in options:
            isOut = False
            start = self.getAmountsOut(
                    val['routers'][0], amount, [val['names'][0],val['names'][1]])
        else:
            start = int(options['out'] * amount)
        prev = start

        rem = item['route'][1:]
        end = len(rem) - 1

        for index, i in enumerate(rem):
            router = val['routers'][index + 1]
        
            # to populate the addresses list
            if index == 0 or rem[index - 1]['via'] != i['via']:
                addr = [tokens[i['from']],tokens[i['to']]]
                addresses.append(router) 
                print(f'addresses snapshot, index {index} :- {addresses}')
            else:
                addr.append(tokens[i['to']])

            # to populate the data list
            if index == end or rem[index + 1]['via'] != i['via']:
                defs, args = ['address[]'], [addr]
                print(f'addr snapshot, index {index} :- {addr}')
                data.append(encode_abi(defs,args))
            
            '''if not isOut:
                step = self.getAmountsOut(
                    val['routers'][index], prev, [tokens[i['from']],tokens[i['to']]])
            else:
                step = int(options['out'][index] * prev)
                prev = step'''

        
        defs = ['address[]','bytes[]','address','uint256','uint256']
        args = [addresses,data,val['pair'],amount,fee]

        #print(args)
        DATA = Web3.toHex(encode_abi(defs,args))

        names = val['names']
        token0 = self.sortTokens(tokens[names[0]],tokens[names[1]])[0]

        AMOUNT0 = start if tokens[names[0]] == token0 else 0
        AMOUNT1 = 0 if tokens[names[0]] == token0 else start

        #print(f'final payload :- {AMOUNT0,AMOUNT1,tokens[names[0]],DATA}')
        return [AMOUNT0,AMOUNT1,tokens[names[0]],DATA]

    def execute(self, payload):
        contract = self.getContract()
        account = self.getAccount()

        if self.isTestnet():
            tranx = contract.functions.start(*payload).transact({'from' : account})
        else:
            rawTx = contract.functions.start(*payload).buildTransaction(
                {'from': account, 
                'nonce': self.web3.eth.get_transaction_count(account.address)}
            )
            txCreate = self.web3.eth.account.sign_transaction(rawTx,self.pv)
            tranx = self.web3.eth.send_raw_transaction(txCreate.rawTransaction)

        txReceipt = self.web3.eth.wait_for_transaction_receipt(tranx)
        print(f'tx succesful with hash: {txReceipt.transactionHash.hex()}')
        
    def arb(self, routes = [], amount = 10,  keyargs = []):
        
        #keyargs is a list of dictionaries
        if not routes:
            routes = self.getRoutes()
        lenght = len(routes)

        if keyargs:
            assert len(keyargs) == lenght

        Prospects = self.getProspect(routes)

        try:
            for i in range(amount):
                print(f'arbing {i + 1} of {lenght} routes')
                prospect = next(Prospects)

                if not keyargs:
                    payload = self.prepPayload(prospect) 
                else:
                    payload = self.prepPayload(prospect,keyargs[i])
                
                if payload: self.execute(payload)

        except StopIteration:
            print('route items exhausted!')

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







