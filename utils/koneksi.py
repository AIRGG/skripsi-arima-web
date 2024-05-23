from typing import List
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker

import os

import pandas as pd

class Connection:
    def __init__(self):
        username = 'postgres'
        password = 'admin123'
        endpoint = 'localhost'
        database_iot = 'dbiot'
        database_iot_helper = 'dbiot_helper'

        self.url_db1 = f"postgresql+asyncpg://{username}:{password}@{endpoint}/{database_iot}"
        self.url_db2 = (
            f"postgresql+asyncpg://{username}:{password}@{endpoint}/{database_iot_helper}"
        )

        self.engine1 = create_async_engine(
            self.url_db1,
            # poolclass=NullPool,
            pool_size=5,
            max_overflow=10,
            # pool_recycle=1,
            # poolclass=QueuePool,
            connect_args={"server_settings": {"jit": "off", "application_name": "iotBE-dbthingsboard"}},
        )
        self.engine2 = create_async_engine(
            self.url_db2,
            # poolclass=NullPool,
            pool_size=5,
            max_overflow=10,
            # pool_recycle=1,
            # poolclass=QueuePool,
            connect_args={"server_settings": {"jit": "off", "application_name": "iotBE-dbhelper"}},
        )

        self.conn1 = self.engine1.connect()
        self.conn2 = self.engine2.connect()

    def get_metadata(self, database=1):
        if database == 1:
            metadata = MetaData()
            metadata.reflect(bind=self.engine1)
        elif database == 2:
            metadata = MetaData()
            metadata.reflect(bind=self.engine2)
        else:
            raise ValueError("Invalid database number")
        return metadata

    async def get_dbsession(self):
        db = async_sessionmaker(
            autocommit=False, expire_on_commit=False, autoflush=False, bind=self.engine1
        )()
        try:
            yield db
        finally:
            await db.close()

    async def get_dbsessionhelper(self):
        db = async_sessionmaker(
            autocommit=False, expire_on_commit=False, autoflush=False, bind=self.engine2
        )()
        try:
            yield db
        finally:
            await db.close()

    def get_engines(self):
        return self.engine1, self.engine2

    async def dispose_engines(self):
        await self.engine1.dispose()
        await self.engine2.dispose()
    
    def pandas_read_sql_query(self, con, stmt):
        return pd.read_sql_query(stmt, con)

    async def df_conniot(self, stmt):
        async with self.engine1.begin() as conn:
            data = await conn.run_sync(self.pandas_read_sql_query, stmt)
        return data
    
    async def df_connhelper(self, stmt):
        async with self.engine2.begin() as conn:
            data = await conn.run_sync(self.pandas_read_sql_query, stmt)
        return data
