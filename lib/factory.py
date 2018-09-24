import lib.api as api
import lib.functions as f
import lib.lookML as l
import configparser as ConfigParser
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('settings/settings.ini')
try:
    import lib.db as db
    #Create a single db instance, accessed globally to save resources
    DB = db.db()
    l.DB_FIELD_DELIMITER_START = DB.literalDelimeterStart
    l.DB_FIELD_DELIMITER_END = DB.literalDelimeterEnd
except:
    logging.info('Failed to import or connect to the DB, operating in offline mode. Obtaining delimiter from config file')
    class db:
        literalDelimeterStart = config.get('db','delimeter_start')
        literalDelimeterEnd = config.get('db','delimeter_end')
    DB = db()

class viewFactory:
    '''
        view factory has 2 primary modes:
        1) DB Driven
            A) Prefetch -- This is fastest when you are generating many tables
            B) Query 1 Table -- This is simple when you are generating only a single table
        2) Looker API Driven
            Requires info schema to be modeled in Looker and available via the api connection configured in settings
            This has the added benefit that no drivers are required to be installed and therefore can work for any Looker DB connection
            **Might be slightly slower than direct DB connection for large numbers of tables
    '''
    def build_info_schema_odbc_prefetch(self, tablePattern=None, catalog=None, schema=None, column=None):
        self.colMap = {}
        for row in DB.getInformationSchemaMap(table=tablePattern, catalog=catalog, schema=schema, column=column):
            if row.table_name in self.colMap.keys():
                self.colMap[row.table_name].append({'schema':row.table_schem , 'col' : row.column_name, 'type' : row.type_name})
            else:
                self.colMap.update({row.table_name: [{'schema':row.table_schem , 'col' : row.column_name, 'type' : row.type_name}]}) 

    def create_view_from_infoschema_cache(self,table=None,schema=None):
            tmpView = l.View(f.lookCase(table))
            # tmpView.setName(f.lookCase(table))
            if table in self.colMap.keys():
                schem = self.colMap[table][0]['schema']
                tmpView.setSqlTableName(
                    sql_table_name=table,schema=schema
                                )
                for field in self.colMap[table]:
                    if field['type'] in ['int','bigint','smallint','double'] :
                        dim = l.Dimension(dbColumn=field['col'])
                        dim.setNumber()
                        tmpView.addField(dim)
                    elif field['type'] in ['char','varchar'] :
                        dim = l.Dimension(dbColumn=field['col'])
                        dim.setString()
                        tmpView.addField(dim)
                    elif field['type'] in ['date','timestamp','time'] :
                        dim = l.DimensionGroup(dbColumn=field['col'])
                        dim.setType('time')
                        tmpView.addField(dim)
                    elif field['type'] in ['bit']:
                        dim = l.Dimension(dbColumn=field['col'])
                        dim.setType('yesno')
                        tmpView.addField(dim)
                return tmpView
            else:
                logging.info(table + " Not Found Skipping view Creation....")
                return None

    def odbc_metadata_mapper(self, tmp, cursor):
        '''Pass a pyodbc cursor object and it will use return values to determine the field types and add each field to the view'''
        for col in cursor:
            if str(col[1]) == "<class 'str'>":
                dim = l.Dimension(dbColumn=col[0])
                dim.setType('string')
                tmp.addField(dim)
            elif str(col[1]) == "<class 'decimal.Decimal'>":
                dim = l.Dimension(dbColumn=col[0])
                dim.setType('number')
                tmp.addField(dim)
            elif str(col[1]) == "<class 'datetime.datetime'>":
                dim = l.DimensionGroup(dbColumn=col[0])
                dim.setType('time')
                tmp.addField(dim)
            elif str(col[1]) == "<class 'int'>":
                dim = l.Dimension(dbColumn=col[0])
                dim.setType('string')  # We used string for int in our POC
                tmp.addField(dim)
            elif str(col[1]) == "<class 'bool'>":
                dim = l.Dimension(dbColumn=col[0])
                dim.setType('string')  # We used string for bool in our POC
                tmp.addField(dim)
        return tmp

    def createViewFromTable(self, sql_table_name):
        ''' pass a table name to the view, use the information to retrieve table metadata and create the view representation '''
        tmp = l.View()
        tmp.tableSource = True
        tmp.sql_table_name = l.Property('sql_table_name', sql_table_name)
        return self.odbc_metadata_mapper(tmp, DB.getTableMetaData(sql_table_name))

    def createViewFromQuery(self, query):
        '''pass a string query, will run against DB and generate fields based on result set. Returns self'''
        tmp = l.View()
        tmp.tableSource = False
        tmp.derived_table = l.Property('derived_table', {'sql': query})
        return self.odbc_metadata_mapper(tmp,DB.getCursorMetaData(query))
    
    def build_info_schema_api_prefetch(self, tablePattern=None, catalog=None, schema=None, column=None):
        tmp = l.View()
        apiInstance = api.lookerAPIClient()
        field_iteration = apiInstance.get_columns(schema=schema, table_name=tablePattern)
        for field in field_iteration:
            if 'NUMBER' in field['Data_Type']:
                dim = l.Dimension(dbColumn=field['Column_Name'])
                dim.setType('number')
                tmp.addField(dim)
        return tmp