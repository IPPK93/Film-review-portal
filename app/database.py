import os

import dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

dotenv.load_dotenv()

db_url = os.environ.get('SQLALCHEMY_DATABASE_URL')
engine = create_engine(db_url, connect_args={'check_same_thread': False})
LocalSession = sessionmaker(bind=engine)
