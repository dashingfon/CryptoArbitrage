import Blockchains as Blc
import utills 



if __name__ == '__main__': 

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

    chain = Blc.Kovan()
    utills.buildData(chain)

        
    
    
    