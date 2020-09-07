import pymysql
import numpy as np
from numpy import ndarray
from typing import List, Tuple
import pandas as pd

opened = 0


class DatabaseController:
    '''Class that handles the communication with a sql database.'''

    @classmethod
    def get_heroku_db(cls) -> 'DatabaseController':
        return cls('b59b25a8f483fb', 'df9f008b', 'heroku_59f0bb8d5ef8c3d', 'us-mm-dca-c6a1e480c80b.g5.cleardb.net')

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
        # print('open connection')
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # print('close connection')
        self.close()

    def __del__(self):
        print('instance removed')
        self.close()

    def open(self):
        '''Open the db cursor & connection.'''
        if self.connection is not None:
            # Cleanup first.
            self.close()
        self.connection = pymysql.connect(user=self.user, password=self.pwd, database=self.db, host=self.host)
        self.cursor = self.connection.cursor()
        # opened += 1
        # print(f'con: {opened}')

    def close(self):
        '''Commit the connection. Then close the db cursor & connection.'''
        if self.connection is None:
            return
        self.connection.commit()
        self.cursor.close()
        self.connection.close()
        self.connection = None
        self.cursor = None
        # opened -= 1
        # print(f'con: {opened}')

    def fetch_one(self, query: str) -> str:
        '''Execute the select statement and read one row of data.'''
        with self:
            self.cursor.execute(query)
            row = self.cursor.fetchone()
            return row
    
    def fetchone(self, query: str):
        return self.fetch_one(query)
    
    def fetch_many(self, query: str) -> List[str]:
        '''Execute the select statement and read all rows of data.'''
        with self:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            return rows
    
    def fetch_as_df(self, query: str) -> pd.DataFrame:
        '''Fetch the given query as a pandas DataFrame.'''
        with self:
            return pd.read_sql(query, self.connection)
    
    def fetch_count(self, case_id: str) -> int:
        '''Fetch the number of records corresponding to the provided case_id.'''
        return self.fetch_one(f"SELECT count(*) FROM data WHERE caseid='{case_id}';")[0]
    
    def fetch_columns(self, table: str) -> List[str]:
        '''Fetch the column names for a given table.'''
        query = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table}' " \
            f"AND TABLE_SCHEMA='{self.db}';"
        return [row[0] for row in self.fetch_many(query)]
    
    def fetch_all_as_df(self, case_id: str, include_egm: bool = True, batch_size: int = 2000) -> pd.DataFrame:
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

    def fetch_all_case_ids(self, condition: str = None) -> List[str]:
        '''Fetch all distinct "caseids" from the data table.'''
        if condition is None:
            query = "SELECT DISTINCT caseid FROM data;"
        else:
            query = f"SELECT DISTINCT caseid FROM data WHERE {condition};"
        return [row[0] for row in self.fetch_many(query)]

    def fetch_ecg(self, case_id: str) -> ndarray:
        '''Fetch the ecg data for the given case_id as a 1d np.ndarray.'''
        row = self.fetch_one(f"SELECT ecg_cs FROM .case WHERE name='{case_id}';")
        return np.fromstring(row[0], sep=' ', dtype=np.float)

    def fetch_labeled_egms(self) -> List[Tuple[ndarray, str, str]]:
        '''Fetch the egm, label, and category as a list of 1d [np.ndarray, str].'''
        rows = self.fetch_many(f"SELECT egm, label, category FROM data WHERE category IS NOT NULL AND new_gt IS NULL;")
        return [[np.fromstring(row[0], sep=' ', dtype=np.float), row[1], row[2]] for row in rows]
    
    def fetch_new_gt_egms(self) -> List[Tuple[ndarray, str]]:
        '''Fetch the egm and new_gt for rows with new_gt.'''
        rows = self.fetch_many('SELECT egm, new_gt FROM data WHERE new_gt IS NOT NULL;')
        return [[np.fromstring(row[0], sep=' ', dtype=np.float), row[1]] for row in rows]
    
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
