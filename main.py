#get imports
import pandas as pd
import pypika
from psycopg import Cursor
from pypika import PostgreSQLQuery, Schema, Column




import psycopg2
################
conn = psycopg2.connect(
    host="localhost",
    database="dvdrental",
    user="postgres",
    password="aakashojha873Qa")
cursor = conn.cursor();
cursor.execute("select * from customer");


conn.close()
##################

conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password="aakashojha873Qa")
cursor = conn.cursor();
cursor.execute("CREATE SCHEMA test1 AUTHORIZATION postgres")
conn.close()

#put parametrers and constants
DVD = ... #this is the path to config file
'''
# This section contains some script parameters
DATABASE_CONFIG = '.config\.postgres'
SECTION = 'postgresql'
The following is the list of the connection parameters:

   database: the name of the database that you want to connect.

   user: the username used to authenticate.
   
   password: password used to authenticate.

   host: database server address e.g., localhost or an IP address.

   port: the port number that defaults to 5432 if it is not provided.
'''



#put etl function
def create_cursor():
    import psycopg2 as pg
    engine = pg.connect("dbname='dvdrental' user='postgres' host='localhost' port='5432' password='aakashojha873Qa'")
    return engine

#reading from the public schema
def read_table(engine):
    import pandas as pd
    df = pd.read_sql('select * from customer', con=engine)
    return df 

def transform_dates(df):
    import datetime
    from datetime import datetime
    df['last_update']= df['last_update'].dt.strftime('%Y-%m-%d')
    df['last_update'] 
    return df
  






#create tasks with etl function
import kans.tasks

def create_task(inputs: Task | Tuple):
    if isinstance(inputs, Task):
        return inputs
    elif isinstance(inputs, tuple):
        return Task(*inputs)
    else:
        raise TypeError('Step must be a Task, Pipeline or Tuple')









#put task in dag(graph.py)
#network x 
#graph.py





#sort dag in topological order
#network x




#put sorted task in a queue
#queue.py




#executor pull tasks off queue and runs them
#combine with scheduler or seprate




#scheduler determines when to run the above
#crontab
#apscheduler
#schedule
#https://apscheduler.readthedocs.io/en/3.x/

if __name__ == '__main__':
    # this part is needed to execute the program
    main()







 
