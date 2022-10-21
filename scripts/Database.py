'''Module containing all the database methods and functions'''

from sqlmodel import (
    SQLModel,
    create_engine,
    Session,
    select,
    inspect,
    Field
    )
from typing import Optional


class Routes(SQLModel):
    '''Route Model class'''
    id: Optional[int] = Field(default=None, primary_key=True)
    simplyfied_Sht: str = Field()
    simplyfied_full: str = Field()
    startToken: str = Field(index=True)
    startExchanges: str = Field(index=True)
    amountOfSwaps: int = Field(index=True)
    time: float = Field(index=True)

    @classmethod
    def fromSwaps(cls, swaps: list) -> 'Routes':

        short, long = [], []
        for j in swaps:
            long.append(f"{j.fro.fullJoin} {j.to.fullJoin} {j.via}")  # noqa: E501
            short.append(f"{j.fro.shortJoin} {j.to.shortJoin} {j.via}")  # noqa: E501

        return cls(
           simplyfied_Sht=' - '.join(short),
           simplyfied_full=' - '.join(long),
           startToken=swaps[0].fro.shortJoin,
           startExchanges=swaps[0].via,
           amountOfSwaps=len(swaps),
           time=time.time()
        )


if __name__ == '__main__':
    import time

    Test = type('Test', (Routes,),
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
