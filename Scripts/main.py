import Blockchains as Blc

if __name__ == '__main__':
    chain = Blc.Aurora()
    #chain = Blc.BSC()
    chain.pollRoutes()