import logging
import requests
import pyodbc 
import configparser as ConfigParser
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('settings/settings.ini')


def db():
    ''' Routes to the appropriate derived type database connection '''
    if 'SQL Server' in config.get('db', 'driver'):
        return sqlServer()
    elif 'postgres' in config.get('db', 'driver'):
        return postgres()
    elif 'MySQL' in config.get('db', 'driver'):
        return mySQL()
    else:
        return database()

class database:
    ''' Abstract Class to define database connection behaviors'''
    def __init__(self, *args, **kwargs):
        self.server   = config.get('db', 'server')
        self.database = config.get('db', 'database')
        self.username = config.get('db', 'username')
        self.password = config.get('db', 'password')
        self.driver   = config.get('db', 'driver')
        self.port   = config.get('db', 'port')
        self.cnxn = self.connect()
        self.cursor = self.cnxn.cursor()
        self.literalDelimeterStart = '`'
        self.literalDelimeterEnd = '`' 
    
    def connect(self):
        return pyodbc.connect(
            'DRIVER='      + self.driver
            + ';SERVER='   + self.server
            + ';DATABASE=' + self.database
            + ';UID='      + self.username
            + ';PWD='      + self.password
            + ';PORT='     + self.port
                    )

    def getCursorMetaData(self,query):
        ''''''
        try:
            self.cursor.execute(query)
            for elem in self.cursor.description:
                yield elem
        except:
            logging.info('Error obtaining metadata via this query:: %s' , query)

    def getData(self, query):
        ''''''
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except:
            logging.info('Error with this query:: %s' , query)
            
    def getTableMetaData(self, table):
        ''''''
        return self.getCursorMetaData('SELECT * FROM ' + table + ' WHERE 1=1 LIMIT 10')

    def getTablePK(self, table, catalog=None, schema=None):
        for row in self.cursor.primaryKeys(table=table, catalog=catalog, schema=schema):
            print(row.column_name)

    def getInformationSchemaMap(self, table=None, catalog=None, schema=None, column=None):
        ''''''
        # return self.cursor.columns(table='vwDimCompany')
        return self.cursor.columns(table=table, catalog=catalog, schema=schema, column=column)

class mySQL(database):
    def __init__(self, *args, **kwargs):
        super(mySQL, self).__init__(self, *args, **kwargs)
        self.literalDelimeterStart = '`'
        self.literalDelimeterEnd = '`'

    def connect(self):
        return pyodbc.connect(
            'DRIVER='      + self.driver
            + ';Data Source='   + self.server
            + ';Database=' + self.database
            + ';User ID='      + self.username
            + ';Password='      + self.password
            + ';PORT='     + self.port
            + ';Login Prompt=False;CHARSET=UTF8'
                    )
#Login Prompt=False;
#User ID=root;Password=root;Data Source=localhost;Database=test;CHARSET=UTF8

#     def getTableMetaData(self, table):
#         return self.getCursorMetaData('SELECT TOP (10) * FROM ' + table + ' WHERE 1=1')

#     def informationSchema(self, tablePattern):
#         return self.getData(f"select * from INFORMATION_SCHEMA.COLUMNS c where c.TABLE_NAME like '{tablePattern}'")


class postgres(database):
    ''' specific implementation for postgres '''
    def __init__(self, *args, **kwargs):
        super(postgres, self).__init__(self, *args, **kwargs)
        self.literalDelimeterStart = '`'
        self.literalDelimeterEnd = '`' 

    def getTableMetaData(self, table):
        return self.getCursorMetaData('SELECT * FROM ' + table + ' WHERE 1=1 LIMIT 10')

    def informationSchema(self, tablePattern):
        return self.getData(f"select * from INFORMATION_SCHEMA.COLUMNS c where c.TABLE_NAME like '{tablePattern}'")