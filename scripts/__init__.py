import logging
import logging.config
import pathlib

path: pathlib.PurePath = pathlib.PurePath(__file__).parent.parent

logging.config.fileConfig(str(path.joinpath("logging.conf")))
CONFIG_PATH = str(path.joinpath('scripts', 'Config.json'))
DATABASE_URL = f"sqlite:///{str(path.joinpath('data', 'Database', 'database.db'))}"  # noqa E501
