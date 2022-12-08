import os
from sqlalchemy import create_engine  
from sqlalchemy.orm import sessionmaker


host = "localhost"
port = 5432
user = "postgres"
password = "aakashojha873Qa"
db = "dvdrental"
dbtype = "postgresql+psycopg2"

SQLALCHEMY_DATABASE_URI = f"{dbtype}://{user}:{password}@{host}:{port}/{db}"

dwEngine1 = create_engine(SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
dwSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dwEngine1)