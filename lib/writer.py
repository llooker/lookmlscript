import jinja2, codecs, os
from jinja2 import Environment, BaseLoader

class templateProcessor:
    def __init__(self 
                ,contextVariables = {}
                ,templatePath     = 'settings/templates/'
                ,template          = ''
                ,outFileName      = ''
                ,outFileExtension = ''
                ,outFileWritePath = ''
                ,*args
                ,**kwargs
                ):
        
        #template
        self.templatePath = templatePath
        self.rawTemplate = template
        self.contextVariables = contextVariables
        self.boundTemplate = None
        
        #outFile
        self.outFileWritePath = outFileWritePath
        self.outFileName      = outFileName
        self.outFileExtension = outFileExtension if outFileExtension else outFileName.split('.')[-1:] #obtain the extension from the name if not provided
        self.outFilePath      = self.outFileWritePath + '/' + self.outFileName + '.' + self.outFileExtension
        
        self.mode = kwargs.get('mode','wb')
        self.encoding = kwargs.get('encoding','utf-8')
        
        self.block_start_string       = kwargs.get('block_start_string'   ,'<%')
        self.block_end_string        = kwargs.get('block_end_string'     ,'%>')
        self.variable_start_string = kwargs.get('variable_start_string','<<')
        self.variable_end_string   = kwargs.get('variable_end_string'  ,'>>')
        self.comment_start_string  = kwargs.get('comment_start_string' ,'<#')
        self.comment_end_string    = kwargs.get('comment_end_string'   ,'#>')
        
    def bindTemplate(self):
        templateEnv = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath = self.templatePath)
            ,extensions=['jinja2.ext.do']
            ,block_start_string       = self.block_start_string
            ,block_end_string        = self.block_end_string 
            ,variable_start_string = self.variable_start_string
            ,variable_end_string   = self.variable_end_string
            ,comment_start_string  = self.comment_start_string
            ,comment_end_string    = self.comment_end_string
                )
        self.boundTemplate = templateEnv.get_template( self.rawTemplate ).render( self.contextVariables )

    def writeFile(self, overWriteExisting=True):
        # if the file doesn't exist, write. If it does, overwrite the existing file if flag allows....
        if not os.path.exists(self.outFilePath) or overWriteExisting:
            f = codecs.open(self.outFilePath, self.mode, self.encoding)
            f.write( self.boundTemplate )
            f.close()

        
    def execute(self):
        self.bindTemplate()
        self.writeFile()
        
        
class stringTemplateProcessor:
    def __init__(self, string, contextVariables, outFilePath, *args, **kwargs):
        self.outFilePath = outFilePath
        rtemplate = Environment(
             loader=BaseLoader
            ,block_start_string      = kwargs.get('block_start_string'   ,'<%')
            ,block_end_string       = kwargs.get('block_end_string'     ,'%>')
            ,variable_start_string = kwargs.get('variable_start_string','<<')
            ,variable_end_string   = kwargs.get('variable_end_string'  ,'>>')
            ,comment_start_string  = kwargs.get('comment_start_string' ,'<#')
            ,comment_end_string    = kwargs.get('comment_end_string'   ,'#>')
            ).from_string(string)
        self.data = rtemplate.render(contextVariables)
        
        self.extension = kwargs.get('extension',".lkml")
        self.mode = kwargs.get('mode', 'wb')
        self.encoding = kwargs.get('encoding', "utf-8")
    
    def boundTemplate(self):
        return self.data
        
    def writeFile(self, overWriteExisting=True):
        # if the file doesn't exist, write. If it does, overwrite the existing file if flag allows....
        if not os.path.exists(self.outFilePath) or overWriteExisting:
            f = codecs.open(self.outFilePath, self.mode, self.encoding)
            f.write( self.boundTemplate() )
            f.close()
        