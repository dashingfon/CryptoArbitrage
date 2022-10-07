'''Module containing all the database methods and functions'''
from sqlmodel import SQLModel, create_engine, Session, select
import scripts.Models as models
import time

filename = "data\\databae.db"
url = f'sqlite:///{filename}'
engine = create_engine(url, echo=True)


def create_db_table():
    SQLModel.metadata.create_all(engine)


def insert_values(*args: dict):
    _1 = models.Routes(
        simplyfied_Sht='yeah', simplyfied_full='nah',
        startToken='BNB', startExchanges='binance',
        amountOfSwaps=6, time=time.time()
    )
    _2 = models.Routes(
        simplyfied_Sht='yeah', simplyfied_full='nah',
        startToken='BNB', startExchanges='binance',
        amountOfSwaps=6, time=time.time()
    )

    with Session(engine) as sess:
        sess.add(_1)
        sess.add(_2)

        sess.commit()


def select_values(selection, where):
    with Session(engine) as sess:
        statement = select(selection).where(where)

        reut = sess.exec(statement)
        print(reut)


if __name__ == '__main__':
    create_db_table()
    # insert_values()
    select_values(
        (models.Routes.amountOfSwaps, models.Routes.id),
        (models.Routes.id <= 2))
