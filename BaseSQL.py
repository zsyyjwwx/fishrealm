from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
HOSTNAME = "localhost"
PORT = 3306
USERNAME = "root"
PASSWORD = ""
DATABASE = "testdb"
CONFIG_KEY = 'SQLALCHEMY_DATABASE_URI'
CONFIG_VALUE = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"

base = declarative_base()
engine = create_engine(CONFIG_VALUE,
        pool_size=100,
        pool_recycle=1600,
        pool_pre_ping=True,
        pool_use_lifo=True,
        echo_pool=True,
        max_overflow=5)
engine.connect()
Session = sessionmaker(bind=engine)
#session = Session()
