import logging
import requests
import pyodbc 
import configparser as ConfigParser
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('/Users/Looker/looker_stuff/msiinformatics/lookmlscript/settings/config.ini')


def db():
    ''' Routes to the appropriate derived type database connection '''
    if 'SQL Server' in config.get('db', 'driver'):
        return sqlServer()
    # elif 'postgres' in config.get('db', 'driver'):
    else:
        return database()

    # "DRIVER={PostgreSQL Unicode};"
    # "DATABASE=postgres;"
    # "UID=postgres;"
    # "PWD=whatever;"
    # "SERVER=localhost;"
    # "PORT=5432;"

class database:
    ''' Abstract Class to define database connection behaviors'''
    def __init__(self, *args, **kwargs):
        self.server   = config.get('db', 'server')
        self.database = config.get('db', 'database')
        self.username = config.get('db', 'username')
        self.password = config.get('db', 'password')
        self.driver   = config.get('db', 'driver')
        self.port   = config.get('db', 'port')
        self.cnxn = pyodbc.connect(
            'DRIVER='      + self.driver
            + ';SERVER='   + self.server
            + ';DATABASE=' + self.database
            + ';UID='      + self.username
            + ';PWD='      + self.password
            + ';PORT='     + self.port
                    )
        self.cursor = self.cnxn.cursor()
        self.literalDelimeterStart = '`'
        self.literalDelimeterEnd = '`' 
        
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

class lookerAPIClient:
    def __init__(self, api_host=None, api_client_id=None, api_secret=None, api_port='19999'):
        auth_request_payload = {'client_id': api_client_id, 'client_secret': api_secret}
        self.host = api_host
        self.uri_stub = '/api/3.0/'
        self.uri_full = ''.join([api_host, ':', api_port, self.uri_stub])
        response = requests.post(self.uri_full + 'login', params=auth_request_payload)
        authData = response.json()
        self.access_token = authData['access_token']
        self.auth_headers = {
                'Authorization' : 'token ' + self.access_token,
                }

    def get(self, call=''):
        response = requests.get(self.uri_full + call, headers=self.auth_headers)
        return response.json()

    def post_test(self, connection, sql):
        response = requests.post(self.uri_full + call, )

    def post(self, connection, sql,  call=''):
        payload = {'connection':connection, 'sql':sql}
        response = requests.post(self.uri_full, data=payload, headers=self.auth_headers)
        return response.json()

    def getLooks(self):
        return self.get('looks')

    def runLook(self, look, limit=100):
        optional_arguments = '?' + 'limit=' + str(limit)
        return self.get('/'.join(['looks',look,'run','json'])+optional_arguments)

    def getlookinfo(self, look):
        return self.get('look')

    def getdashboardinfo(self, dashboard_id):
        return self.get('/'.join(['dashboards',dashboard_id]))

    def createSQLQuery(self,slug):
        return self.post('sql_queries', slug=slug)

    def connection_name(self,fields):
        return self.get(''.join(['/connections','?fields=',fields]))

    def lookmlmodel_info(self,modelname):
        return self.get('/'.join(['lookml_models',modelname]))

#Initialize the Looker API Class with the data in our config file (which is stored in a neighboring file 'config')
x = lookerAPIClient(
        api_host      = config.get('api', 'api_host'), 
        api_client_id = config.get('api', 'api_client_id'), 
        api_secret    = config.get('api', 'api_secret'), 
        api_port      = config.get('api', 'api_port')
        ) 

# print(x)

look_params = {'connection':'snowflake_test', 'sql':'select * from fruit_basket'}

print(x.post('sql_queries', 'snowflake','select test'))

# # class sqlServer(database):
#     ''' specific implementation for SqlServer '''
#     def __init__(self, *args, **kwargs):
#         super(sqlServer, self).__init__(self, *args, **kwargs)
#         self.literalDelimeterStart = '['
#         self.literalDelimeterEnd = ']' 

#     def getTableMetaData(self, table):
#         return self.getCursorMetaData('SELECT TOP (10) * FROM ' + table + ' WHERE 1=1')

#     def informationSchema(self, tablePattern):
#         return self.getData(f"select * from INFORMATION_SCHEMA.COLUMNS c where c.TABLE_NAME like '{tablePattern}'")


# class postgres(database):
#     ''' specific implementation for postgres '''
#     def __init__(self, *args, **kwargs):
#         super(sqlServer, self).__init__(self, *args, **kwargs)
#         self.literalDelimeterStart = '`'
#         self.literalDelimeterEnd = '`' 

#     def getTableMetaData(self, table):
#         return self.getCursorMetaData('SELECT * FROM ' + table + ' WHERE 1=1 LIMIT 10')

#     def informationSchema(self, tablePattern):
#         return self.getData(f"select * from INFORMATION_SCHEMA.COLUMNS c where c.TABLE_NAME like '{tablePattern}'")