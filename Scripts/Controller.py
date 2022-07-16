import web3
import Config as Cfg


def lookupPrice():
    #returns the updated price as a dict
    pass

class Controller():
    def __init__(self,blockchain):
        self.target = 1000
        self.blockchainMap = Cfg.ControllerBlockchains

        if str(blockchain) in self.blockchainMap:
            self.blockchain = blockchain
        else:
            raise ValueError('Invalid Blockchain Object')

    def setup(self):
        pass

    def refresh(self):
        pass
    
    def getRoutes(self, via = 'pollResult'):
        if via == 'pollResult':
            pass


        elif via == 'arbRoute':
            pass
        
        else:
            raise ValueError('Invalid Route Location')

    def check(self, route):
        pass

    def getProspect(self):
        pass

    def prepPayload(self, route):
        pass

    def execute(self):
        pass
