import Config as Cfg
import Controller as Ctr
import requests, json


class Aurora():
    
    def __init__(self):
        self.source = 'https://explorer.mainnet.aurora.dev/api'
        self.slipage = 0.005
        self.dexFees = 0.003
        self.exchanges = Cfg.AuroraExchanges
        self.tokens = Cfg.AuroraTokens
        self.routePath = r'Data\Aurora\arbRoute.json'
        self.params = Cfg.AuroraParams
        self.headers = Cfg.AuroraHeaders
        # the depth limited search depth
        self.depthLimit = 4
        self.graph = {}
        self.arbRoutes = []

    def getPrice(self, session, address):
        parameters = self.params
        parameters['address'] = address
        response = session.get(self.source, headers = self.headers, params = parameters)

        if response.status_code == 200:
            for i in response.json()['result']:
                pass

    def buildPrice(self):
        pass
    
    def buildGraph(self):
        graph = {}
        for dex, tokens in self.exchanges.items():
            for pools in tokens.keys():
                pool = list(pools)
                if pool[0] not in graph:
                    graph[pool[0]] = []
                if pool[1] not in graph:
                    graph[pool[1]] = []
                
                graph[pool[0]].append({'to' : pool[1], 'via' : dex})
                graph[pool[1]].append({'to' : pool[0], 'via' : dex})

        self.graph = graph    

    def dive(self, depth, node, goal, path, followed):
        result = []
        if depth <= self.depthLimit and node in self.graph:
            for i in self.graph[node]:
                if frozenset([i['to'],i['via'],path[-1]['to']]) in followed:
                    pass
                elif i['to'] == goal:
                    new_path = path + [i]
                    new_path[-1]['from'] = new_path[-2]['to']
                    result.append(new_path)
                elif depth < self.depthLimit:
                    followed.append(frozenset([i['to'],i['via'],path[-1]['to']]))
                    new_path = path + [i]
                    new_path[-1]['from'] = new_path[-2]['to']
                    result += self.dive(depth + 1, i['to'], goal,new_path, followed)
        
        return result

    def DLS(self,goal):
        # implementation of depth limited search
        result = []
        path = {'from': goal}
        followed = []
        depth = 1

        if goal in self.graph:
            start = self.graph[goal]
        else:
            start = []

        for i in start:
            followed.append(frozenset([goal,i['to'],i['via']]))
            new_path = [{**path, **i}]
            # recursive function to search the node to the specified depth
            result += self.dive(depth + 1, i['to'],goal,new_path,followed)
        
        return result
           
    def getArbRoute(self, tokens = [],save = True):
        route = []

        if not tokens:
            tokens = self.tokens.keys()
    
        for token in tokens:
            route += self.DLS(token)
    
        if save:
            with open(self.routePath,'w') as AR:
                json.dump(route,AR,indent = 2)
        else:
            return route
        
    def pollRoute(self, route):
        rates = []
        liquidityList = []
        least = 0
        numerator = 0
        denumerator = 0
        lenght = len(route)

        for index, swap in enumerate(route):

            if index == 0:
                pass
            elif index == lenght - 1:
                pass
            else:
                pass

        return [least, numerator/denumerator]

    def pollRoutes(self, routes = []):
        if not routes:
            with open(self.routePath) as RO:
                routes = json.load(RO)

        result = []

        for route in routes:
            capital, index = self.pollRoute(route)
            result.append({
                'index' : index,
                'maxCapital' : capital
            })

        return result
    
    def screenRoutes(self, capital = 100, index = 1.1, routes = [], save = True):
        newRoute = []
        if not routes:
            with open(self.routePath) as RO:
                routes = json.load(RO)

        for route in routes:
            capital, index = self.pollRoute(route)


        if save:
            with open(self.routePath,'w') as AR:
                json.dump(newRoute,AR,indent = 2)
        else:
            return routes    

    def executeArb(self, routes = []):
        pass


Aurora = Aurora()
Aurora.buildGraph()
#print(Aurora.graph)
Aurora.getArbRoute(tokens = Cfg.startTokens)
    
          


