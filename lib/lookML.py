
import sys
# sys.path.append('../')
import codecs
import os
import logging
# import configparser as ConfigParser
# config = ConfigParser.RawConfigParser(allow_no_value=True)
# config.read('settings/settings.ini')
import lib.functions as f

import lib.writer as writer
import lib.api as api
try:
    import lib.db as db
    #Create a single db instance, accessed globally to save resources
    DB = db.db()
except:
    logging.info('Failed to import or connect to the DB, operating in offline mode')
    class db:
        literalDelimeterStart = '`'
        literalDelimeterEnd = '`'
    DB = db()

"""
Author:			Russell Garner
Created Date:	2017
Description:	This module is for create lookml scripts.

Change
Author			Date 			Description
------------------------------------------------------
BoRam Hong		2018.01.11		Adding int and bool data type to View metaDataMapper method
								Change snakeCase method to lookCase method to remove spaces on view name.
"""

#Class that doesn't get instantiated on it's own, rather serves as an input to several other classes e.g. view, model 
class lookMLObject:
    def __init__(self, *args, **kwargs):
        self.extension = kwargs.get('extension', '.lkml')
        self.outFilePath = kwargs.get('outFilePath', 'lookMLObject.lkml')
        self.contextVariables = kwargs.get('contextVariables', {})
        
        #self.outFileFolder = kwargs.get('outPath', 'output')
        #set the name first from an explicit named argument of either identifier or name, 
        # otherwise check for the first positional argument, if it is a string use it otherwise empty string
        self.fileName = ''
        self.identifier = kwargs.get('identifier', None)
        if not self.identifier:
            self.identifier = kwargs.get('name', None)
        if not self.identifier:
            if len(args) > 1:
                if isinstance(args[1],str):
                    self.identifier = args[1]
            else:
                self.identifier = ''

    def setOutFilePath(self, outFilePath, objectNameAsFileName=True):
        ''''''
        if objectNameAsFileName:
            if isinstance(self,View):
                self.fileName = self.identifier + '.view.lkml'
                self.outFilePath = '/'.join([outFilePath,self.identifier + '.view.lkml'])
            elif isinstance(self, Model):
                self.fileName = self.identifier + '.model.lkml'
                self.outFilePath = '/'.join([outFilePath,self.fileName])
            else:
                self.fileName = self.identifier + '.lkml'
                self.outFilePath = '/'.join([outFilePath,self.fileName])
        else:
            self.outFilePath = outFilePath
        return self

    def setName(self, identifier):
        ''''''
        self.identifier = identifier
        return self

    def writeFile(self,overWriteExisting=True):
        ''' Checks to see if the file exists before writing'''
        w = writer.stringTemplateProcessor(
            string=self.__str__(),
            contextVariables=self.contextVariables,
            outFilePath=self.outFilePath
        )
        w.writeFile(overWriteExisting=overWriteExisting)


## Schema = a dict that relates to the available options within a Lookml object, (e.g. check quickhelp in Looker IDE for available options or docs for more options)
class View(lookMLObject):
    __slots__ = ['sql_table_name','derived_table','tableSource','message','fields','primaryKey','schema','properties','children','parent']
    def __init__(self, *args, **kwargs):
        ### fileProperties ###
        if 'sql_table_name' in kwargs.keys():
            self.sql_table_name = Property('sql_table_name', kwargs.get('sql_table_name', 'view'))
            self.tableSource = True
        elif 'derived_table' in kwargs.keys():
            self.derived_table = Property('derived_table', kwargs.get('derived_table', 'view'))
            self.tableSource = False
        else:
            self.tableSource = None
        self.message = kwargs.get('message', '')
        self.fields = {}
        self.primaryKey = ''
        self.schema = kwargs.get('schema', {})
        self.properties = Properties(self.schema)
        self.children = {}
        self.parent = None
        super(View, self).__init__(self, *args, **kwargs)

    def __str__(self):
        return f.splice(
                        f.splice('#',self.message,'\n') if self.message else '', 
                        'view: ', self.identifier, ' {', 
                        '\n',self.source(),'\n', 
                        '\n'.join([str(p) for p in self.properties.getProperties()]), 
                        '\n    '.join([str(field) for field in self.getFieldsSorted()]), 
                        '\n}\n',
                        *[str(child) for child in self.children.values()] if self.children else ''
                        )

    def __repr__(self):
        return "%s (%r) fields: %s" % (self.__class__, self.identifier, len(self)) 

    def __len__(self):
        return len([f for f in self.getFields()])

    def __add__(self,other):
        if isinstance(other, Field):
            return self.addField(other)
        elif isinstance(other, str):
            return self.addDimension(dbColumn=other)
        else: 
            raise Exception(str(type(other)) + ' cannot be added to View')

    def __radd__(self,other):
        return self.__add__(other)

    def __sub__(self,other):
        if isinstance(other, Field):
            return self.removeField(other)
        elif isinstance(other, str):
            return self.removeField(other)
        elif isinstance(other,View):
            return self.children.pop(other.identifier,None)
        else: 
            raise Exception(str(type(other)) + ' cannot be subtracted from View')

    def __rsub__(self,other):
        return self.__sub__(other)

    def __invert__(self):
        ''' hides all dimensions (not measures) '''
        for dim in self.getDimensions():
            dim.hide()
        for dim in self.getDimensionGroups():
            dim.hide()
        for dim in self.getParameters():
            dim.hide()
        for dim in self.getFilters():
            dim.hide()
        return self

    def __contains__(self,item):
        return item in self.fields.keys()

    def __getitem__(self,identifier):
        return self.getField(identifier)

    def __getattr__(self, key):
        if key == 'name':
            return self.identifier
        elif key == 'pk':
            return self.getPrimaryKey()
        elif key == 'ref':
            return f.splice('${',self.identifier,'}')
        else:
            return self.__getitem__(key)

    def __setattr__(self, name, value):
        if name == 'label':
            self.setLabel(value)
            return self
        elif name == 'name':
            self.setName(value)
            return self
        elif name == 'pk':
            self.setPrimaryKey(value)
            return self
        else:
            object.__setattr__(self, name, value)

    def source(self):
        if self.tableSource == None:
            return ''
        elif self.tableSource == False:
            return str(self.derived_table)
        else:
            return str(self.sql_table_name)

    def setSqlTableName(self,sql_table_name):
        ''' Set the sql table name, returns self'''
        self.sql_table_name = Property('sql_table_name',sql_table_name)
        self.tableSource = True
        self.derived_table = None
        return self

## Method adds a commented message at the top of a view
    def setMessage(self, message):
        '''Sets a Commented Message above the view'''
        self.message = ''.join(['#', message])
        return self

## Method will take an inputted string and add that property to the schema dict of the view using the addProperty method.
    def setLabel(self, label):
        ''' Sets the view label property'''
        self.properties.addProperty('label',label)
        return self

## Method returns true or false, if used will add extension required parameter
## addProperty method, takes a dictionary as an input and adds to the 'schema'
    def setExtensionRequired(self):
        ''' Sets the view to be "extension: required" '''
        self.properties.addProperty('extension','required')
        return self    

    def getFields(self):
        '''Returns all the fields as a generator'''
        for field, literal in self.fields.items():
            ## Does this yeild only return the first value of this loop?
            yield literal

    def getFieldsSorted(self):
        ''' returns all the fields sorted first by alpabetical dimensions/filters, then alphabetical measures '''
        return sorted(self.fields.values(), key=lambda field: ''.join([str(isinstance(field, Measure)), field.identifier]))

    def getFieldNames(self):
        ''' Returns field names/identifiers as a generator yielding strings '''
        for field, literal in self.fields.items():
            yield field

    def getField(self, identifier):
        ''' Returns a specific field based on identifier/string lookup'''
        return self.fields.get(identifier, Field(identifier='Not Found'))

    def getFieldByDBColumn(self, dbColumn):
        ''' Converts the db column to lookCase for identifier lookup.....'''
        #TODO: re-implement this to actually use the DB column as a key (keep in mind that doesn't need to be unique...)
        #TODO: Raise a not found exception here instead of silently failing with a notfound key
        return self.fields.get(f.lookCase(dbColumn), Field(identifier='Not Found'))

    def addField(self, field):
        '''Takes a field object as an argument and adds it to the view, if the field is a dimension and primary key it will be set as the view primary key'''
        # uses the 'setView' method on field which returns self so that field can fully qualify itself and so that field can be a member of view
        self.fields.update({field.identifier: field.setView(self)})
        # If a primary key is added it will overwrite the existing primary key....
        if isinstance(field, Dimension):
            if field.isPrimaryKey():
                self.setPrimaryKey(field.identifier)
        return self
    
    def removeField(self,field):
        '''Removes a field, either by object or by string of identifier, safely checks and de-refs primary key'''
        def pk(k):
            if k.isPrimaryKey:
                self.unSetPrimaryKey()
        if isinstance(field,Field):
            if isinstance(field,Dimension):
                pk(field)
            pk(self.getField(field.identifier))
            return self.fields.pop(field.identifier, None)
        elif isinstance(field,str):
            dimToDel = self.getField(field)
            if isinstance(dimToDel,Dimension):
                pk(dimToDel)
            return self.fields.pop(field, None)
        else:
            raise Exception('Not a string or Field instance provided')

    def addFields(self, fields):
        ''' An iterable collection of field objects will be passed to the add field function. Helpful for adding many fields at once'''
        for field in fields:
            self.addField(field)
        return self

    def setPrimaryKey(self, f, callFromChild=False):
        ''' A string identifier or a field object can be passed, and will be set as the new primary key of the view'''
        self.unSetPrimaryKey()
        if isinstance(f, Dimension):
            if not callFromChild:
                f.setPrimaryKey()
            self.primaryKey = f.identifier
        else:
            tmpField = self.getField(f)
            if isinstance(tmpField, Dimension):
                self.primaryKey = tmpField.identifier
                if not callFromChild:
                    tmpField.setPrimaryKey()
                    # tmpField.setPrimaryKey()
        return self

    def getPrimaryKey(self):
        '''returns the primary key'''
        if self.primaryKey:
            return self.getField(self.primaryKey)

    def unSetPrimaryKey(self):
        '''Unsets the view primary key returns self'''
        pk = self.getField(self.primaryKey)
        if isinstance(pk, Dimension):
            pk.unSetPrimaryKey()
        self.primaryKey = ''
        return self

    def getDimensions(self):
        '''returns iterable of Dimension Fields'''
        return filter(lambda dim: isinstance(dim, Dimension), self.fields.values())

    def getDimensionGroups(self):
        '''returns iterable of DimensionGroup Fields'''
        return filter(lambda dim: isinstance(dim, DimensionGroup), self.fields.values())

    def getMeasures(self):
        '''returns iterable of Measure Fields'''
        return filter(lambda meas: isinstance(meas, Measure), self.fields.values())

    def getFilters(self):
        '''returns iterable of Filter Fields'''
        return filter(lambda fil: isinstance(fil, Filter), self.fields.values())

    def getParameters(self):
        '''returns iterable of Paramter Fields'''
        return filter(lambda par: isinstance(par, Parameter), self.fields.values())

    def metaDataMapper(self, cursor):
        '''Pass a pyodbc cursor object and it will use return values to determine the field types and add each field to the view'''
        for col in cursor:
            if str(col[1]) == "<class 'str'>":
                dim = Dimension(dbColumn=col[0])
                dim.setType('string')
                self.addField(dim)
            elif str(col[1]) == "<class 'decimal.Decimal'>":
                dim = Dimension(dbColumn=col[0])
                dim.setType('number')
                self.addField(dim)
            elif str(col[1]) == "<class 'datetime.datetime'>":
                dim = DimensionGroup(dbColumn=col[0])
                dim.setType('time')
                self.addField(dim)
            elif str(col[1]) == "<class 'int'>":
                dim = Dimension(dbColumn=col[0])
                dim.setType('string')  # We used string for int in our POC
                self.addField(dim)
            elif str(col[1]) == "<class 'bool'>":
                dim = Dimension(dbColumn=col[0])
                dim.setType('string')  # We used string for bool in our POC
                self.addField(dim)

    def createViewFromTable(self, sql_table_name):
        ''' pass a table name to the view, use the information to retrieve table metadata and create the view representation '''
        self.tableSource = True
        self.sql_table_name = Property('sql_table_name', sql_table_name)
        self.metaDataMapper(DB.getTableMetaData(sql_table_name))
        return self

    def createViewFromQuery(self, query):
        '''pass a string query, will run against DB and generate fields based on result set. Returns self'''
        self.tableSource = False
        self.derived_table = Property('derived_table', {'sql': query})
        self.metaDataMapper(DB.getCursorMetaData(query))
        return self

    def addDimension(self,dbColumn, type='string'):
        ''' dbColumn is a string representing the column name'''
        dim = Dimension(dbColumn=dbColumn)
        dim.setType(type)
        self.addField(dim)
        return self

    def addCount(self):
        '''Add a count measure to the view, returns self'''
        measure = Measure(
            identifier='count', schema={'type': 'count'}
        )
        self.addField(measure)
        return self

    def addCountDistinct(self, f):
        '''Add a count distinct to the view based on a field object or field name/identifier. returns self'''
        if isinstance(f, Field):
            field = f
        else:
            field = self.getField(f)
        measure = Measure(
            identifier=''.join(['count_distinct_', field.identifier]), schema={'sql': field.ref_short}
        )
        measure.setType('count_distinct')
        self.addField(measure)
        return self

    def addSum(self, f):
        '''Add a count distinct to the view based on a field object or field name/identifier. returns self'''
        if isinstance(f, Field):
            field = f
        else:
            field = self.getField(f)
        measure = Measure(
            identifier=''.join(['total_', field.identifier]), schema={'sql': field.ref_short}
        )
        measure.setType('sum')
        self.addField(measure)
        return self

    def extend(self, name='', sameFile=True, required=False, *args):
        ''' Creates an extended view, optionally within the same view file 
            name (string) -> name of the extended / child view. Will default to the parent + _extended
            sameFile (boolean) -> default true, if true will result in the child being printed within the parent's string call / file print
            required (boolean) -> default false, if true will result in the parent being set to extension required
            returns the child view object
        '''
        
        if not name:
            if len(args) > 1:
                if isinstance(args[0],str):
                    child = View(args[0])
                else:
                    child = View('_'.join([self.identifier,'extended'])) 
            else:
                child = View('_'.join([self.identifier,'extended']))
        else:
            child = View(name)

        if required:
            self.setExtensionRequired()
        child.properties.addProperty('extends',self.identifier)
        child.parent = self
        if sameFile:
            self.children.update({child.identifier: child})
        return child


class Join:
    ''' Instantiates a LookML join object... '''
    __slots__ = ['properties', 'identifier','_from','to']

    def __init__(self, *args, **kwargs):
        self.properties = Properties(kwargs.get('schema', {}))
        self.identifier = kwargs.get('identifier', kwargs.get('view', 'error_view_not_set'))
        self._from = kwargs.get('from', None)
        self.to = kwargs.get('to', None)

    def __str__(self):
        return f.splice(
                         '\njoin: ', self.identifier, ' {\n    ',
                         '\n    '.join([str(p) for p in self.properties.getProperties()]),
                         '\n}\n'
                          )

    def setName(self, identifier):
        self.identifier = identifier
        return self

    def setOn(self,sql_on):
        self.properties.addProperty('sql_on', sql_on )
        return self

    def setType(self, joinType):
        assert joinType in ['left_outer','full_outer','inner','cross']
        self.properties.addProperty('type',joinType)
        return self


class Explore:
    ''' Represents an explore object in LookML'''
    def __init__(self, *args, **kwargs):
        self.properties = Properties(kwargs.get('schema', {}))
        # self.identifier = kwargs.get('identifier', kwargs.get('view', 'error_view_not_set'))
        self.joins = dict()
        self.base_view = kwargs.get('view',None)

        self.identifier = kwargs.get('identifier', None)
        if not self.identifier:
            self.identifier = kwargs.get('name', None)
        if not self.identifier:
            if len(args) >= 1:
                if isinstance(args[0],str):
                    self.setName(args[0])
                elif isinstance(args[0],View):
                    self.setName(args[0].name)


        self.view = kwargs.get('view', '')

    def __str__(self):
        return f.splice(
                    '\nexplore: ', self.identifier, ' {\n    ', 
                    '\n    '.join([str(p) for p in self.properties.getProperties()]), 
                    '\n    '.join([str(join) for join in self.getJoins()]),
                     '\n}\n'
                     )

    def __add__(self,other):
        if isinstance(other,View):
            pass 
        elif isinstance(other,Join):
            pass
        return self

    def setName(self,name):
        self.identifier = name
        return self

    def setViewName(self,view):
        self.properties.addProperty('view_name',view)

    def addJoin(self, join):
        self.joins.update({join.identifier, join})

    def getJoins(self):
        for field, literal in self.joins.items():
            yield literal

    def getJoin(self, key):
        return self.joins.get(key, {})



class Model(lookMLObject):
    def __init__(self, *args, **kwargs):
        super(Model, self).__init__(self, *args, **kwargs)
        self.schema = kwargs.get('schema', {})
        self.properties = Properties(self.schema)
        self.explores = {}

    def __str__(self):
        return f.splice(
                        '\n'.join([str(p) for p in self.properties.getProperties()]), 
                        '\n' * 5, '\n'.join([str(e) for e in self.getExplores()])
                        )
    def setConnection(self,value):
        self.properties.addProperty('connection',value)
        return self

    def include(self,file):
        if isinstance(file,lookMLObject):
            self.properties.addProperty('include',file.fileName)
        else:
            self.properties.addProperty('include',file) 
        return self 

    def setName(self, name):
       self.setIdentifier(name)
       return self

    def addExplore(self, explore):
        self.explores.update({explore.identifier: explore})

    def getExplores(self):
        for field, literal in self.explores.items():
            yield literal

    def getExplore(self, key):
        return self.explores.pop(key, {})


class Field:
    ''' Base class for fields in LookML, only derived/child types should be instantiated '''
    __slots__ = ['schema', 'properties','db_column','identifier','view']
    def __init__(self, *args, **kwargs):
        self.schema = kwargs.get('schema', {})
        self.properties = Properties(self.schema)
        self.db_column = kwargs.get('dbColumn', '')

        self.identifier = kwargs.get('identifier', None)
        if not self.identifier:
            self.identifier = kwargs.get('name', None)
        if not self.identifier:
            if len(args) > 1:
                if isinstance(args[1],str):
                    self.setName(args[1])
            elif self.db_column:
                self.identifier = f.lookCase(self.db_column)
            else:
                self.identifier = ''

        self.view = kwargs.get('view', '')
        
    def __str__(self):
        return f.splice(
                        self.identifier, ' {\n    ', 
                            '\n    '.join([str(n) for n in self.properties.getProperties()]),
                            '\n}\n'
                         )

    def __getattr__(self, key):
        if key == 'name':
            return self.identifier
        elif key == 'pk':
            return self.getPrimaryKey()
        elif key == 'ref':
            if self.view:
                return f.splice('${' , self.view.identifier , '.' , self.identifier , '}')
        elif key == 'ref_short':
            return f.splice('${' , self.identifier , '}')
        else:
            pass

    def __setattr__(self, name, value):
        if name == 'label':
            self.setLabel(value)
            return self
        elif name == 'name':
            self.setName(value)
            return self
        else:
            object.__setattr__(self, name, value)

    def setView(self, view):
        ''''''
        self.view = view
        return self  # satisfies a need to linkback (look where setView is called)

    def setName(self,identifier):
        self.identifier = identifier
        return self

    def setDBColumn(self, dbColumn, changeIdentifier=True):
        ''''''
        self.db_column = dbColumn
        if changeIdentifier:
            self.identifier = f.lookCase(self.db_column)
        return self

    def setProperty(self, name, value):
        ''''''
        self.properties.addProperty(name, value)
        return self

    def unSetProperty(self, name):
        ''''''
        self.properties.delProperty(name)
        return self

    def getProperty(self, identifier):
        ''''''
        return self.properties.getProperty(identifier)

    def setType(self, type):
        ''''''
        self.properties.addProperty('type', type)
        return self

    def setNumber(self):
        ''''''
        return self.setType('number')

    def setString(self):
        ''''''
        return self.setType('string')

    def setLabel(self, label):
        ''''''
        return self.setProperty('label', label)

    def setViewLabel(self, viewLabel):
        ''''''
        return self.setProperty('view_label', viewLabel)

    def hide(self):
        ''''''
        self.properties.addProperty('hidden', 'yes')
        return self

    def unHide(self):
        ''''''
        self.properties.delProperty('hidden')
        return self



class Property:
    ''' A basic property / key value pair. 
    If the value is a dict it will recusively instantiate properties within itself '''
    __slots__ = ['name', 'value']
    def __init__(self, name, value):
        self.name = name
        if isinstance(value, str):
            self.value = value
        elif isinstance(value, dict):
            self.value = Properties(value)
        else:
            raise Exception('not a dict or string')

    def __str__(self):
        if self.name.startswith('sql') or self.name == 'html':
            return f.splice(self.name, ': ', str(self.value), ' ;;')
        elif self.name in ['include', 'connection', 'description','value']:
            return f.splice(self.name, ': "', str(self.value), '"')
        elif self.name.endswith('url') or self.name.endswith('label') or self.name.endswith('format') or self.name.endswith('persist_for'):
            return f.splice(self.name, ': "', str(self.value), '"')
        elif self.name == 'extends':
            return f.splice(self.name, ': [', str(self.value), ']')
        elif self.name.startswith('filters'):
            return f.splice(f.stripID(self.name),str(self.value))
        else:
            return f.splice(self.name , ': ' , str(self.value))


class Properties:
    '''
    Treats the collection of properties as a recursive dicitionary
    Things that fall outside of uniqueness (special cases):
    includes, links, filters, bind_filters
    Things that should be their own class:
    data_groups, named_value_format, sets
    '''
    __slots__ = ['schema']

    def __init__(self, schema):
        assert isinstance(schema, dict)
        self.schema = schema

    def __str__(self):
        return f.splice(
                        '{\n' , 
                        '\n    '.join([str(p) for p in self.getProperties()]) ,
                         '\n}' 
                         )

    def getProperty(self, identifier):
        return Property(identifier, self.schema.get(identifier, None))

    def getProperties(self):
        for k, v in self.schema.items():
            yield Property(k, v)

    def addProperty(self, name, value):
        if name == 'includes':
            n = len([x for x in filter(lambda x: x.startswith('includes'), self.schema.keys())])
            self.schema.update({name +'_'+str(n) : value})
        elif name == 'links': 
            n = len([x for x in filter(lambda x: x.startswith('links'), self.schema.keys())])
            self.schema.update({name +'_'+str(n) : value})            
        elif name == 'filters':
            n = len([x for x in filter(lambda x: x.startswith('filters'), self.schema.keys())])
            self.schema.update({name +'_'+str(n) : value})            
        elif name == 'bind_filters':
            n = len([x for x in filter(lambda x: x.startswith('bind_filters'), self.schema.keys())])
            self.schema.update({name +'_'+str(n) : value})
        else:
            self.schema.update({name: value})

    def delProperty(self, identifier):
        self.schema.pop(identifier, None)

    def isMember(self, property):
        return property in self.schema.keys()


class Dimension(Field):
    def __init__(self, *args, **kwargs):
        ### SUPER CALL ####
        super(Dimension, self).__init__(self, *args, **kwargs)
        if not self.properties.isMember('sql'):
            self.properties.addProperty('sql', f.splice('${TABLE}.' , DB.literalDelimeterStart , self.db_column , DB.literalDelimeterEnd))

    def isPrimaryKey(self):
        if self.properties.isMember('primary_key') and self.properties.getProperty('primary_key').value == 'yes':
            return True
        else:
            return False

    def setPrimaryKey(self):
        self.setProperty('primary_key', 'yes')
        self.view.setPrimaryKey(self.identifier, callFromChild=True)
        return self

    def unSetPrimaryKey(self):
        self.unSetProperty('primary_key')
        return self

    def setTier(self, tiers=[]):
        if tiers:
            self.setProperty('tiers', '[0,5,10,15,20]')
        else:
            self.setProperty('tiers', '[' + ','.join(tiers) + ']')
        return self.setType('tier')

    def __str__(self):
        return f.splice(
                        '\ndimension: ', 
                        super(Dimension, self).__str__()
                        )


class DimensionGroup(Field):
    def __init__(self, *args, **kwargs):
        ### SUPER CALL ####
        super(DimensionGroup, self).__init__(self, *args, **kwargs)
        if not self.properties.isMember('timeframes'):
            self.properties.addProperty('timeframes', '[raw, year, quarter, month, week, date, day_of_week, hour, hour_of_day, minute, time, time_of_day]')
        if not self.properties.isMember('type'):
            self.properties.addProperty('type', 'time')
        if not self.properties.isMember('sql'):
            self.properties.addProperty('sql', f.splice('${TABLE}.' , DB.literalDelimeterStart , self.db_column , DB.literalDelimeterEnd))

    def __str__(self):
        return f.splice(
                        '\ndimension_group: ', 
                        super(DimensionGroup, self).__str__()
                        )


class Measure(Field):
    def __init__(self, *args, **kwargs):
        ### SUPER CALL ####
        super(Measure, self).__init__(self, *args, **kwargs)

    def __str__(self):
        return f.splice(
                        '\nmeasure: ', 
                        super(Measure, self).__str__()
                        )


class Filter(Field):
    def __init__(self, *args, **kwargs):
        ### SUPER CALL ####
        super(Filter, self).__init__(self, *args, **kwargs)

    def __str__(self):
        return f.splice(
                        '\nfilter: ', 
                        super(Filter, self).__str__()
                        )


class Parameter(Field):
    def __init__(self, *args, **kwargs):
        ### SUPER CALL ####
        super(Parameter, self).__init__(self, *args, **kwargs)

    def __str__(self):
        return f.splice(
                        '\nparameter: ', 
                        super(Parameter, self).__str__()
                        )

class viewFactory:
    ''' Does one information Schema Lookup based on a passed table pattern, returns generator of Views. DB connection must be working'''
    def __init__(self, tablePattern=None, catalog=None, schema=None, column=None):
        self.colMap = {}
        for row in DB.getInformationSchemaMap(table=tablePattern, catalog=catalog, schema=schema, column=column):
            if row.table_name in self.colMap.keys():
                self.colMap[row.table_name].append({'schema':row.table_schem , 'col' : row.column_name, 'type' : row.type_name})
            else:
                self.colMap.update({row.table_name: [{'schema':row.table_schem , 'col' : row.column_name, 'type' : row.type_name}]}) 
    
    def createView(self,table=None,schema=None):

            tmpView = View()
            tmpView.setName(f.lookCase(table))
            if table in self.colMap.keys():
                schem = self.colMap[table][0]['schema']
                if schema:
                    tmpView.setSqlTableName(
                                    f.splice(
                                        DB.literalDelimeterStart,
                                        schema,
                                        DB.literalDelimeterEnd,
                                        '.',
                                        DB.literalDelimeterStart,
                                        table,
                                        DB.literalDelimeterEnd
                                        )
                                    )
                else:
                    tmpView.setSqlTableName(
                    f.splice(
                        DB.literalDelimeterStart,
                        table,
                        DB.literalDelimeterEnd
                        )
                    ) 
                for field in self.colMap[table]:
                    if field['type'] in ['int','bigint','smallint','double'] :
                        dim = Dimension(dbColumn=field['col'])
                        dim.setNumber()
                        tmpView.addField(dim)
                    elif field['type'] in ['char','varchar'] :
                        dim = Dimension(dbColumn=field['col'])
                        dim.setString()
                        tmpView.addField(dim)
                    elif field['type'] in ['date','timestamp','time'] :
                        dim = DimensionGroup(dbColumn=field['col'])
                        dim.setType('time')
                        tmpView.addField(dim)
                    elif field['type'] in ['bit']:
                        dim = Dimension(dbColumn=field['col'])
                        dim.setType('yesno')
                        tmpView.addField(dim)
                return tmpView
            else:
                logging.info(table + " Not Found Skipping view Creation....")
                return None

class viewFactory2:
    '''
        This is an alternative implementation which derives metadata from the looker API only
        '''
    def __init__(self):
         pass


    
    def createView(self, tablePattern=None, catalog=None, schema=None, column=None):
        tmp = View()
        apiInstance = api.lookerAPIClient()
        field_iteration = apiInstance.get_columns(schema=schema, table_name=tablePattern)
        for field in field_iteration:
            if 'NUMBER' in field['Data_Type']:
                dim = Dimension(dbColumn=field['Column_Name'])
                dim.setType('number')
                tmp.addField(dim)
        return tmp