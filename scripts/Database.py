'''Module containing all the database methods and functions'''

from sqlmodel import SQLModel, create_engine, Session, select, inspect


if __name__ == '__main__':
    import time
    import scripts.Models as models
    Test = type('Test', (models.Routes,),
            {'__tablename__': 'Test'}, table=True)  # noqa

    filename = "data\\databae.db"
    url = f'sqlite:///{filename}'
    engine = create_engine(url, echo=True)

    def create_db_table():
        SQLModel.metadata.create_all(engine)

    def insert_values(override: bool = False):
        if override and inspect(engine).has_table('Test'):
            Test.__table__.drop(engine)  # type: ignore
        create_db_table()

        _1 = Test(
            simplyfied_Sht='yeah', simplyfied_full='nah',
            startToken='ETH', startExchanges='binance',
            amountOfSwaps=4, time=time.time()
        )
        _2 = Test(
            simplyfied_Sht='yeah', simplyfied_full='nah',
            startToken='ETH', startExchanges='binance',
            amountOfSwaps=6, time=time.time()
        )

        with Session(engine) as sess:
            sess.add(_1)
            sess.add(_2)

            sess.commit()

    def select_values(selection, where):
        with Session(engine) as sess:
            raw = select(*selection)

            statement = raw
            for i in where:
                statement = statement.where(i)

            ''' reut = sess.exec(statement)
            for r in reut:
                print(r)'''
            print(list(sess.exec(statement)))

    create_db_table()
    insert_values(override=True)

    '''select_values(
        (Test.startToken, Test.amountOfSwaps),
        (Test.amountOfSwaps >= 5, Test.startToken == 'ETH'))
'''
