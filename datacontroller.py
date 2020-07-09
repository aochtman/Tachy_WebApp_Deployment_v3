import pymysql
import numpy as np
from numpy import ndarray
from typing import List
import pandas as pd

class DatabaseController:
    '''Class that handles the communication with a sql database.'''

    heroku_db = None

    @classmethod
    def get_heroku_db(cls) -> 'DatabaseController':
        if cls.heroku_db is None:
            cls.heroku_db = cls('b59b25a8f483fb', 'df9f008b', 'heroku_59f0bb8d5ef8c3d', 'us-cdbr-iron-east-05.cleardb.net')
        return cls.heroku_db

    cursor = None
    connection = None

    def __init__(self, user: str = 'root', pwd: str = '', db: str = 'tachy', host: str = 'localhost'):
        '''Init with user, password, database name and host address. Defaults to local mysql instance.'''
        self.user: str = user
        self.pwd: str = pwd
        self.db: str = db
        self.host: str = host

    # Auto-cleanup using `with`.
    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        '''Open the db cursor & connection.'''
        if self.connection is not None:
            # Cleanup first.
            self.close()
        self.connection = pymysql.connect(user=self.user, password=self.pwd, database=self.db, host=self.host)
        self.cursor = self.connection.cursor()

    def close(self):
        '''Commit the connection. Then close the db cursor & connection.'''
        self.connection.commit()
        self.cursor.close()
        self.connection.close()
        self.connection = None
        self.cursor = None

    def execute(self, query: str):
        with self:
            with self.connection:
                self.cursor.execute(query)

    def fetch_one(self, query: str) -> str:
        '''Execute the select statement and read one row of data.'''
        with self:
            with self.connection:
                self.cursor.execute(query)
                row = self.cursor.fetchone()
                return row
    
    def fetch_many(self, query: str) -> List[str]:
        '''Execute the select statement and read all rows of data.'''
        with self:
            with self.connection:
                self.cursor.execute(query)
                rows = self.cursor.fetchall()
                return rows
    
    def fetch_all_case_ids(self) -> List[str]:
        '''Fetch all distinct "caseids" from the data table.'''
        return [row[0] for row in self.fetch_many("SELECT DISTINCT caseid FROM data;")]
    
    def fetch_count(self, case_id: str) -> int:
        '''Fetch the number of records corresponding to the provided case_id.'''
        return self.fetch_one(f"SELECT count(*) FROM data WHERE caseid='{case_id}';")[0]
    
    def fetch_columns(self, table: str) -> List[str]:
        '''Fetch the column names for a given table.'''
        query = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table}';"
        return [row[0] for row in self.fetch_many(query)]
    
    def fetch_as_df(self, sql: str) -> pd.DataFrame:
        with self:
            return pd.read_sql(sql, self.connection)

    def fetch_all_as_df(self, case_id: str, include_egm: bool = True, batch_size: int = 5000) -> pd.DataFrame:
        '''Fetch all columns of records with the specified case_id into a pd.DataFrame.'''
        # first obtain the total cnt of records to be fetched
        total_cnt = self.fetch_count(case_id)
        # generate list of offsets for queries
        batch_offsets = range(0, total_cnt, batch_size)
        n_batches = len(batch_offsets)
        print(f'[fetch_all_as_df] {total_cnt} records divided into {n_batches} chunks, fetching...')
        columns = self.fetch_columns('data')
        if not include_egm:
            del columns[columns.index('egm')]
        print(f'[fetch_all_as_df] selected columns: {columns}')
        columns_str = ','.join(columns)
        # fetch each batch of size <= batch_size
        table = None
        for i, offset in enumerate(batch_offsets):
            lower_id = offset + 1
            upper_id = min(offset + batch_size, total_cnt)
            chunk = self.fetch_many(f"SELECT {columns_str} FROM data WHERE caseid='{case_id}' AND id>={lower_id} AND id<={upper_id};")
            print(f'[fetch_all_as_df] got chunk {i+1:02d}/{n_batches:02d}')
            if table is None:
                table = chunk
            else:
                table += chunk
        return pd.DataFrame(table, columns=columns)

    def fetch_ecg(self, case_id: str) -> ndarray:
        '''Fetch the ecg data for the given case_id as a 1d np.ndarray.'''
        row = self.fetch_one(f"SELECT ecg_cs FROM .case WHERE name='{case_id}';")
        return np.fromstring(row[0], sep=' ', dtype=np.float)

    def fetch_egms(self, case_id: str) -> List[ndarray]:
        '''Fetch the egm data for the given case_id as a list of 1d np.ndarray.'''
        rows = self.fetch_many(f"SELECT egm FROM data where caseid='{case_id}';")
        return [np.fromstring(row[0], sep=' ', dtype=np.float) for row in rows]
    
    def update_ecg_cs(self, case_id: str, ecg_cs_str: str):
        '''Update the ecg_cs column of the case table for the given case_id.'''
        self.__batch_update('.case', ['name', 'ecg_cs'], [[case_id, ecg_cs_str]])

    def __batch_update(self, table: str, columns: List[str], values: List[List[str]]):
        '''The actual implementation of batch_update which the user-facing function below calls.'''
        with self:
            # Prepare the substitutions.
            placeholders = ','.join(['%s'] * len(columns))
            mappings = ','.join(['{0}=VALUES({0})'.format(column) for column in columns])
            columns = ','.join(columns)
            # Generate full sql statement.
            query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {mappings};'
            # Now use executemany as per normal and get the actual speed up of inserts.
            self.cursor.executemany(query, values)
    
    def batch_update(self, table: str, columns: List[str], values: List[List[str]], batch_size: int = 20000):
        '''Perform speedy batch updates into the table, with the given columns and values.
        Values should be a list of lists, each inner list representing a single row of values.
        Note that this function would automatically chunk data into sets of batch_size (defaults 20k).
        '''
        # chunk data according to batch_size
        chunks = []
        for start_index in range(0, len(values), batch_size):
            end_index = min(len(values), start_index + batch_size)
            chunks.append(values[start_index:end_index])
        print(f'[batch_update] Data divided into {len(chunks)} chunks of {batch_size}, now uploading.')
        for i, chunk in enumerate(chunks):
            print(f'[batch_update] Uploading chunk {i+1:02d}/{len(chunks):02d}')
            self.__batch_update(table, columns, chunk)
