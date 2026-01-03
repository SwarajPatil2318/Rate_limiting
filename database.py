from sqlalchemy import create_engine,Column,Integer,String

from sqlalchemy.orm import sessionmaker,declarative_base

DATABASE_URL = "mysql+pymysql://root:swaraj123@db:3306/user_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit = False, autoflush= False,bind=engine)
Base = declarative_base()

