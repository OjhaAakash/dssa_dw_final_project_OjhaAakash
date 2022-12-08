from multiprocessing import connection
import pandas as pd
from psycopg import Cursor
from pypika import PostgreSQLQuery, Schema, Column
from kans.workflows import Pipeline
from kans.tasks import Task
from kans.clients.postgres import PostgresClient
from kans.plotting import plot_dag
from kans.dbengine import dwEngine
from kans.dbengine2 import dwEngine1
from datetime import datetime


#reading from the public schema
def read_table(test_engine):
    df = pd.read_sql("SELECT * FROM public", con=test_engine)
    return df 

def transform_dates(df):
    df['last_update']= df['last_update'].dt.strftime('%Y-%m-%d')
    df['last_update'] 
    return df

def write_table(df):
    df = pd.write_sql('SELECT ')
''' 
connection = dwEngine1.connect()
result = connection.execute("SELECT * FROM public.actor ORDER BY actor_id ASC LIMIT 10")
connection.close()
'''
def main():
    result = read_table(dwEngine1)
    print(result['first_name'])

def test():
    result = read_table()
    



#put task in dag(graph.py)
# This section contains some script parameters
DATABASE_CONFIG = '.config\.postgres'
SECTION = 'postgresql'
DW = Schema('DSSA')
DVD = Schema('public')

# The fact Table of our star schema

FACT_RENTAL = (
    Column('sk_customer', 'INT', False),
    Column('sk_date', 'INT', False),
    Column('sk_store', 'INT', False),
    Column('sk_film', 'INT', False),
    Column('sk_staff', 'INT', False),
    Column('count_rentals', 'INT', False)
)

# A dimension Table for customers
DIM_CUSTOMER = (
    Column('sk_customer', 'INT', False),
    Column('name', 'VARCHAR(100)', False),
    Column('email', 'VARCHAR(100)', False)
)

# A dimension Table for staff
DIM_STAFF = (
    Column('sk_staff', 'INT', False),
    Column('name', 'VARCHAR(100)', False),
    Column('email', 'VARCHAR(100)', False)
)

# A dimension table for films
DIM_FILM = (
    Column('sk_film', 'INT', False),
    Column('rating_code', 'VARCHAR(20)', False),
    Column('film_duration', 'INT', False),
    Column('rental_duration', 'INT', False),
    Column('language', 'CHAR(20)', False),
    Column('release_year', 'INT', False),
    Column('title', 'VARCHAR(255)', False)
)

# A dimension table for dates
DIM_DATE = (
    Column('sk_date', 'INT', False),
    Column('date', 'TIMESTAMP', False),
    Column('quarter', 'INT', False),
    Column('year', 'INT', False),
    Column('month', 'INT', False),
    Column('day', 'INT', False),
)

# A dimension table for stores
DIM_STORE = (
    Column('sk_store', 'INT', False),
    Column('name', 'VARCHAR(100)', False),
    Column('address', 'VARCHAR(50)', False),
    Column('city', 'VARCHAR(50)', False),
    Column('state', 'VARCHAR(20)', False),
    Column('country', 'VARCHAR(50)', False)    
)


# ============================ FUNCTIONS ============================ #
# This section contains all the ETL code that needs to be executed to build a star schema
# The are all python functions that use mostly pandas dataframes for constructing the
# transformed data that will be loaded to the data warehouse.

def create_cursor(path:str, section:str) -> Cursor:
    """Creates a Database Cursor for sending commands
    and queries to the connection instance
    Args:
        path (str): path to an ini file containing database params
        section (str): section name in the ini file containing pararms
    Returns:
        Cursor: A Cursor instance
    """
    client = PostgresClient()
    conn = client.connect_from_config(path, section, autocommit=True)
    cursor = conn.cursor()
    return cursor
    

def create_schema(cursor:Cursor, schema_name:str) -> Cursor:
    """Creates a new schema in a database using a cursor
    Args:
        cursor (Cursor): a cursor instance
        schema_name (str): name of the schema to create
    Returns:
        Cursor: Cursor for sending commands\
            and queries to the connection instance
    """
    q = f"CREATE SCHEMA IF NOT EXISTS {schema_name};"
    cursor.execute(q)
    return cursor


def create_table(
    cursor:Cursor, 
    table_name:str, 
    definition:tuple, 
    primary_key:str=None, 
    foreign_keys:list=None,
    reference_tables:list=None) -> None:
    """Creates a new table in  database using a cursor
    Args:
        cursor (Cursor): cursor instance
        table_name (str): name of the table to create
        definition (tuple): definition of the table to create
        primary_key (str, optional): Primary Key of the Table. Defaults to None.
        foreign_keys (list, optional): Foreign Keys of the Table. Defaults to None.
        reference_tables (list, optional): Reference Table for foreign keys. Defaults to None.
    """
    
    ddl = PostgreSQLQuery \
        .create_table(table_name) \
        .if_not_exists() \
        .columns(*definition)

    if primary_key is not None:
        ddl = ddl.primary_key(primary_key)
        
    if foreign_keys is not None:
        for idx, key in enumerate(foreign_keys):
            ddl.foreign_key(
                columns=key,
                reference_table=reference_tables[idx],
                reference_columns=key
        )
    
    ddl = ddl.get_sql()

    cursor.execute(ddl)
    return


def read_table(cursor:Cursor, table_name:str, columns:tuple) -> pd.DataFrame:
    """Executes a query to selects Columns and rows from a Table using a cursor 
    Args:
        cursor (Cursor): A cursor instance
        table_name (str): name of the table to query
        columns (tuple): name of columns from the table to select
    Returns:
        pd.DataFrame: Returns results in a pandas dataframe
    """
    query = PostgreSQLQuery \
        .from_(table_name) \
        .select(*columns) \
        .get_sql()
    res = cursor.execute(query)
    data = res.fetchall()
    col_names = []
    for names in res.description:
        col_names.append(names[0])
    df = pd.DataFrame(data, columns=col_names)
    return df


def build_dim_customer(cust_df:pd.DataFrame) -> pd.DataFrame:
    """constructs the customer dimension object
    Args:
        cust_df (pd.DataFrame): dataframe from the raw customer table \
            that is usually the result of read_table
    Returns:
        pd.DataFrame: customer dimension object as a pandas dataframe
    """
    cust_df.rename(columns={'customer_id': 'sk_customer'}, inplace=True)
    cust_df['name'] = cust_df.first_name + " " + cust_df.last_name
    dim_customer = cust_df[['sk_customer', 'name', 'email']].copy()
    dim_customer.drop_duplicates(inplace=True)
    return dim_customer
    

def build_dim_staff(staff_df:pd.DataFrame) -> pd.DataFrame:
    """constructs the staff dimension object
    Args:
        staff_df (pd.DataFrame): dataframe from the raw staff table \
            that is usually the result of read_table
    Returns:
        pd.DataFrame: staff dimension object as a pandas dataframe
    """
    staff_df.rename(columns={'staff_id': 'sk_staff'}, inplace=True)
    staff_df['name'] = staff_df.first_name + " " + staff_df.last_name
    dim_staff = staff_df[['sk_staff', 'name', 'email']].copy()
    dim_staff.drop_duplicates(inplace=True)
    return dim_staff
    

def build_dim_dates(dates_df:pd.DataFrame) -> pd.DataFrame:
    """constructs the dates dimension table
    Args:
        dates_df (pd.DataFrame): dataframe from the raw rental table \
            that is usually the result of read_table. The DVD rental \
            database does not have dates table so one is derived.
    Returns:
        pd.DataFrame: date dimension object as a pandas dataframe
    """
    dates_df = dates_df.copy()
    dates_df['sk_date'] = dates_df.rental_date.dt.strftime("%Y%m%d").astype('int')
    dates_df['date'] = dates_df.rental_date.dt.date
    dates_df['quarter'] = dates_df.rental_date.dt.quarter
    dates_df['year'] = dates_df.rental_date.dt.year
    dates_df['month'] = dates_df.rental_date.dt.month
    dates_df['day'] = dates_df.rental_date.dt.day
    dim_dates = dates_df[['sk_date', 'date', 'quarter', 'year', 'month', 'day']].copy()
    dim_dates.drop_duplicates(inplace=True)
    return dim_dates


def build_dim_store(
    store_df:pd.DataFrame, 
    staff_df:pd.DataFrame, 
    address_df:pd.DataFrame,
    city_df:pd.DataFrame,
    country_df:pd.DataFrame) -> pd.DataFrame:
    """constructs the store dimension table
    Args:
        store_df (pd.DataFrame): dataframe from the raw store table
        staff_df (pd.DataFrame): dataframe from the raw staff table
        address_df (pd.DataFrame): dataframe from the raw address table
        city_df (pd.DataFrame): dataframe from the raw city table
        country_df (pd.DataFrame): dataframe from the raw country table
    Returns:
        pd.DataFrame: store dimension object as a pandas dataframe
    """
    
    staff_df.rename(columns={'manager_staff_id':'staff_id'}, inplace=True)
    staff_df['name'] = staff_df.first_name + " " + staff_df.last_name
    staff_df = staff_df[['staff_id', 'name']].copy()
    
    country_df = country_df[['country_id', 'country']].copy()
    city_df = city_df[['city_id', 'city', 'country_id']].copy()
    city_df = city_df.merge(country_df, how='inner', on='country_id')
    
    address_df = address_df[['address_id', 'address', 'district', 'city_id']].copy()
    address_df = address_df.merge(city_df, how='inner', on='city_id')
    address_df.rename(columns={'district': 'state'}, inplace=True)
    
    store_df.rename(columns={'manager_staff_id':'staff_id'}, inplace=True)
    store_df.rename(columns={'store_id': 'sk_store'}, inplace=True)
    store_df = store_df.merge(staff_df, how='inner', on='staff_id')
    store_df = store_df.merge(address_df, how='inner', on='address_id')
    store_df = store_df[['sk_store', 'name', 'address', 'city', 'state', 'country']].copy()
    return store_df


def build_dim_film(film_df:pd.DataFrame, lang_df:pd.DataFrame) -> pd.DataFrame:
    """constructs the film dimension table
    Args:
        film_df (pd.DataFrame): dataframe from the raw film table
        lang_df (pd.DataFrame): dataframe from the raw language table
    Returns:
        pd.DataFrame: film dimension object as a pandas dataframe
    """
    
    film_df.rename(
        columns={'film_id': 'sk_film', 'rating':'rating_code', 'length':'film_duration'},
        inplace=True
        )
    
    lang_df.rename(
        columns={'name':'language'},
        inplace=True
        )
    
    film_df = film_df.merge(lang_df, how='inner', on='language_id')
    film_df = film_df[['sk_film', 'rating_code', 'film_duration', 'rental_duration', 'language', 'release_year', 'title']].copy()
    return film_df


def build_fact_rental(
    rental_df:pd.DataFrame,
    inventory_df:pd.DataFrame,
    date_df:pd.DataFrame,
    film_df:pd.DataFrame,
    staff_df:pd.DataFrame,
    store_df:pd.DataFrame) -> pd.DataFrame:
    """_summary_
    Args:
        rental_df (pd.DataFrame): dataframe from the raw rental table
        inventory_df (pd.DataFrame): dataframe from the raw inventory table
        date_df (pd.DataFrame): dataframe containing dim table
        film_df (pd.DataFrame): dataframe containing dim film
        staff_df (pd.DataFrame): dataframe containing dim staff
        store_df (pd.DataFrame): dataframe containing dim store
    Returns:
        pd.DataFrame: fact rental object as a pandas dataframe
    """
    
    rental_df.rename(columns={'customer_id':'sk_customer', 'rental_date':'date'}, inplace=True)
    rental_df['date'] = rental_df.date.dt.date
    rental_df = rental_df.merge(date_df, how='inner', on='date')
    rental_df = rental_df.merge(inventory_df, how='inner', on='inventory_id')
    rental_df = rental_df.merge(film_df, how='inner', left_on='film_id', right_on='sk_film')
    
    rental_df = rental_df.merge(staff_df, how='inner', left_on='staff_id', right_on='sk_staff')
    rental_df = rental_df.merge(store_df, how='inner', on='name')
    
    rental_df = rental_df.groupby(
        ['sk_customer', 'sk_date', 'sk_store', 'sk_film', 'sk_staff']).agg(count_rentals=('rental_id','count')).reset_index()
    
    rental_df = rental_df[['sk_customer', 'sk_date', 'sk_store', 'sk_film', 'sk_staff', 'count_rentals']].copy()
    return rental_df


def sink_data(cursor: Cursor, df:pd.DataFrame, target:str):
    """Writes data to a table from a pandas dataframe
    Args:
        cursor (Cursor): A cusror instance
        df (pd.DataFrame): pandas dataframe containing data to write 
        target (str): name of table for "INSERT" query
    """
    data = tuple(df.itertuples(index=False, name=None))
    query = PostgreSQLQuery \
        .into(target) \
        .insert(*data) \
        .get_sql()
    cursor.execute(query)
    return 


def tear_down(cursor: Cursor) -> None:
    """Closes the connection to the Database
    Args:
        cursor (Cursor): Cursor instance
    """
    # Uncomment below to remove everyting created from this pipeline
    #cursor.execute("DROP SCHEMA "DSSA" CASCADE;")
    cursor.close()
    return



def main():
    # ============================ AUTHORING WORKFLOWS ============================ #
    # This section uses maellin's Pipeline class to author a DAG based workflow
    # from the functions defined above. Note that merging multiple pipelines together
    # is natively supported. When a Task with a dependency is created, the Pipeline calls
    # the Task.validate() on the dependency to check for compatibility before it is added 
    # to the DAG. Compatibility checks rely on type hints for all provided arguments
    # and return statements. To skip validation simply set skip_validation=True when
    # creating the Task. 
    
    # Creates a DAG for all the DDL commands to execute to create schema and tables
    setup_workflow = Pipeline(
        steps=[
            Task(create_cursor, 
                 kwargs={'path': "/Users/aakashojha/Documents/Stockton/Aakash final project/dssa_dw_final_project_OjhaAakash/dssa_dw_final_project_OjhaAakash/DATABASE_CONFIG", 'section': "SECTION"}, 
                 depends_on=None, 
                 name='create_cursor'),
            Task(create_schema, 
                 kwargs={"schema_name": "DSSA"}, 
                 depends_on=['create_cursor'], 
                 name='create_schema'),
            Task(create_table,
                 kwargs={'table_name': "DSSA.customer",'primary_key':'sk_customer', 'definition':DIM_CUSTOMER}, 
                 depends_on=['create_schema'], 
                 name='create_dim_customer'),
            Task(create_table, 
                 kwargs={'table_name': "DSSA.store", 'primary_key':'sk_store', 'definition':DIM_STORE},
                 depends_on=['create_schema'],
                 name='create_dim_store'),
            Task(create_table,
                 kwargs={'table_name': "DSSA.film", 'primary_key':'sk_film', 'definition': DIM_FILM}, 
                 depends_on=['create_schema'],
                 name='create_dim_film'),
            Task(create_table,
                 kwargs={'table_name': "DSSA.staff", 'primary_key':'sk_staff', 'definition':DIM_STAFF}, 
                 depends_on=['create_schema'],
                 name='create_dim_staff'),
            Task(create_table,
                 kwargs={'table_name': "DSSA.date", 'primary_key':'sk_date', 'definition': DIM_DATE},
                 depends_on=['create_schema'],
                 name='create_dim_dates'),
            Task(create_table,
                kwargs={
                    'table_name': "DSSA.factRental", 'definition':FACT_RENTAL,
                    'foreign_keys':['sk_customer', 'sk_store', 'sk_film', 'sk_staff', 'sk_date'],
                    'reference_tables': ["DSSA.customer", "DSSA.store", "DSSA.film", "DSSA.staff", "DSSA.date"]},
                depends_on=['create_schema'],
                name='create_fact_rentals')
        ],
        type='default'
    )
    
    # Creates a DAG for extract, transform, and load to dim Customer
    cust_workflow = Pipeline(
        steps=[
            Task(read_table,
                 kwargs={'table_name': "DVD.customer",'columns': ('customer_id', 'first_name', 'last_name', 'email')},
                 depends_on=['create_cursor'],
                 name='extract_cust'
                 ),
            Task(build_dim_customer,
                 depends_on=['extract_cust'],
                 name='transf_cust'
                 ),
            Task(sink_data,
                 depends_on=['create_cursor','transf_cust', 'create_dim_customer'],
                 kwargs={'target': "DSSA.customer"},
                 name='load_customer',
                 skip_validation=True
                 )
            ]
        )
    
    # Creates a DAG for extract, transform, and load to dim Staff
    staff_workflow = Pipeline(
        steps=[
            Task(read_table,
                kwargs={'table_name': "DVD.staff",'columns': ('staff_id', 'first_name', 'last_name', 'email')},
                depends_on=['create_cursor'],
                name='extract_staff'
                ),
            Task(build_dim_staff,
                 depends_on=['extract_staff'],
                 name='transf_staff'
                 ),
            Task(sink_data,
                 depends_on=['create_cursor','transf_staff', 'create_dim_staff'],
                 kwargs={'target': "DSSA.staff"},
                 name='load_staff',
                 skip_validation=True
                 )
            ]
        )
    
    # Creates a DAG for extract, transform, and load to dim Dates
    dates_workflow = Pipeline(
        steps=[
            Task(read_table,
                 kwargs={'table_name': "DVD.rental",'columns': ('rental_id', 'rental_date', 'inventory_id', 'staff_id', 'customer_id')},
                 depends_on=['create_cursor'],
                 name='extract_dates'
                 ),
            Task(build_dim_dates,
                 depends_on=['extract_dates'],
                 name='transf_dates'
                 ),
            Task(sink_data,
                 depends_on=['create_cursor','transf_dates', 'create_dim_dates'],
                 kwargs={'target': "DSSA.date"},
                 name='load_dates',
                 skip_validation=True
                 ),
            ]
        )

    # Creates a DAG for extract, transform, and load to dim Store
    store_workflow = Pipeline(
        steps=[
            Task(read_table,
                 kwargs={'table_name': "DVD.store",'columns': ('store_id','manager_staff_id', 'address_id')},
                 depends_on=['create_cursor'],
                 name='extract_store'
                 ),
            Task(read_table,
                 kwargs={'table_name': "DVD.address",'columns': ('address_id','address', 'city_id', 'district')},
                 depends_on=['create_cursor'],
                 name='extract_address'
                 ),
            Task(read_table,
                 kwargs={'table_name': "DVD.city",'columns': ('city_id','city', 'country_id')},
                 depends_on=['create_cursor'],
                 name='extract_city'
                 ),
            Task(read_table,
                 kwargs={'table_name': "DVD.country",'columns': ('country_id','country')},
                 depends_on=['create_cursor'],
                 name='extract_country'
                 ),
            Task(build_dim_store,
                 depends_on=['extract_store', 'extract_staff', 'extract_address', 'extract_city', 'extract_country'],
                 name='transf_store'
                 ),
            Task(sink_data,
                 depends_on=['create_cursor','transf_store', 'create_dim_store'],
                 kwargs={'target': "DSSA.store"},
                 name='load_store',
                 skip_validation=True
                 ),
            ]
        )
    
    # Creates a DAG for extract, transform, and load to dim Film
    film_workflow = Pipeline(
        steps=[
            Task(read_table,
                kwargs={'table_name': "DVD.film",'columns': (
                    'film_id', 'rating', 'length', 'rental_duration', 'language_id','release_year', 'title')},
                depends_on=['create_cursor'],
                name='extract_film'
                ),
            Task(read_table,
                kwargs={'table_name': "DVD.language",'columns': ('language_id', 'name')},
                depends_on=['create_cursor'],
                name='extract_language'
                ),
            Task(build_dim_film,
                 depends_on=['extract_film', 'extract_language'],
                 name='transf_film'
                 ),
            Task(sink_data,
                 depends_on=['create_cursor','transf_film', 'create_dim_film'],
                 kwargs={'target': "DSSA.film"},
                 name='load_film',
                 skip_validation=True
                 )
        ]
    )
    
    # Creates a DAG for extract, transform, and load to Fact Rental
    fact_workflow = Pipeline(
        steps=[
            Task(read_table,
                kwargs={'table_name': "DVD.inventory",'columns': ('inventory_id', 'film_id', 'store_id')},
                depends_on=['create_cursor'],
                name='extract_inventory'
                ),
            Task(build_fact_rental,
                 depends_on=['extract_dates', 'extract_inventory', 'transf_dates', 'transf_film', 'transf_staff', 'transf_store'],
                 name='transf_fact_rental'
                 ),
            Task(sink_data,
                 depends_on=['create_cursor','transf_fact_rental', 'create_fact_rentals'],
                 kwargs={'target': "DSSA.factRental"},
                 name='load_fact_rental',
                 skip_validation=True
                 )
        ]
    )
    
    # Creates a DAG for tear down tasks and closing out any open connections to the database
    teardown_workflow = Pipeline(
        steps =[
            Task(tear_down,
                depends_on= [
                    'create_cursor', 
                    film_workflow, 
                    store_workflow, 
                    dates_workflow, 
                    staff_workflow, 
                    cust_workflow, 
                    fact_workflow],
                name='tear_down',
                skip_validation=True)
            ]
        )


    # We merge all the above Pipelines into a single Pipeline containing all Tasks to be added to the DAG.
    workflow = Pipeline(
        steps=[
            setup_workflow,
            cust_workflow,
            staff_workflow,
            dates_workflow,
            store_workflow,
            film_workflow,
            fact_workflow,
            teardown_workflow
        ]
    )


    # ============================ COMPILATION ============================ #
    # This section composes the DAG from the provided Tasks 
    workflow.compose()
    # Optionally we can plot the DAG (this module needs work bewarned)
    #plot_dag(etl_workflow.dag, savefig=False, path='dag.png')
    
    # Save the DAG so that it can be scheduled
    workflow.dump(filename='/Users/aakashojha/Documents/Stockton/Aakash final project/dssa_dw_final_project_OjhaAakash/xyz.txt')



    # ============================ ENQUEUE ============================ #
    # This section uses the .collect() method which enqueues all tasks in the DAG
    # to a task FIFO queue in topological order 
    workflow.collect()


    # ============================ EXECUTION ============================ #
    # Runs a KANS Workflow locally using a single worker
    # This option is good for debugging before presisting the workflow 
    # and submitting it to the scheduler.
    workflow.run()
    
import os
import time
from kans   .workflows import Pipeline
from kans.scheduler import DefaultScheduler

sched = DefaultScheduler()
sched.start()
    
def create_jobs(path_to_dags:str):
    """Adds All Stored DAGs to The Scheduler"""
         
def main():

    
    # Poll Scheduler for scheduled dag runs
    while True:
        create_jobs('.dags')
        sched.print_jobs()
        time.sleep(5)
    

connection.commit

if __name__ == '__main__':
    main()
