'''Module containing all the database methods and functions'''
from sqlmodel import SQLModel, create_engine, Session, select
import scripts.Models as models
import time

filename = "data\\databae.db"
url = f'sqlite:///{filename}'
engine = create_engine(url, echo=True)


def create_db_table():
    SQLModel.metadata.create_all(engine)


def insert_values():
    _1 = models.Routes(
        simplyfied_Sht='yeah', simplyfied_full='nah',
        startToken='ETH', startExchanges='binance',
        amountOfSwaps=4, time=time.time()
    )
    _2 = models.Routes(
        simplyfied_Sht='yeah', simplyfied_full='nah',
        startToken='ETH', startExchanges='binance',
        amountOfSwaps=6, time=time.time()
    )

    with Session(engine) as sess:
        sess.add(_1)
        sess.add(_2)

        sess.commit()


def select_values(selection, *where):
    with Session(engine) as sess:
        raw = select(*selection)

        if not where:
            statement = raw
        for i in where:
            statement = raw.where(i)

        ''' reut = sess.exec(statement)
        for r in reut:
            print(r)'''
        print(list(sess.exec(statement)))


if __name__ == '__main__':
    create_db_table()
    # insert_values()
    select_values(
        (models.Routes.startToken, models.Routes.amountOfSwaps),
        (models.Routes.amountOfSwaps >= 2),
        (models.Routes.startToken == 'ETH'))
