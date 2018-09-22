#!/usr/bin/env python3
# -- #!/usr/bin/env python
import lib.lookML 
import lib.writer 
import lib.db as db
import lib.gitController
import logging
import os 
import lib.functions as f
import requests

logging.basicConfig(
                filename='logs/log.log', 
                format='%(levelname)s:%(asctime)s %(message)s', 
                datefmt='%m/%d/%Y %I:%M:%S %p', 
                level=20
                            )
FIRST_RUN = True

if __name__ == '__main__':
    git = lib.gitController.gitController(projectName='mylookerproject1', branch='master') #will create a folder in the output directory to contain the cloned project
    git.clone('git@github.com:russlooker/lookmlscript_test_project.git') ## Your Existing lookml project

    myView  = lib.lookML.View() #Instantiate the view
    myView.setSqlTableName('public.order_items') 
    myView.setName('myViewName')
    myView.addDimension('id')
    myView.addDimension('value')
    myView.addSum(myView['value'])
    myView['value'].hide()

    myView.addCountDistinct(myView['id'])
    myView.setOutFilePath(git.absoluteOutputPath)
    myView.writeFile(overWriteExisting=True)

    if FIRST_RUN:
        tenants = ['tennat1','tennat2','tennat3']
        for tenant in tenants:
            templateContext = {
                "tenant": tenant,
                "additional_join_flag":True
                #,Hypothetical other variables you want to pass into the template renderer
            }
            w = lib.writer.templateProcessor(
                    contextVariables = templateContext
                    ,templatePath     = 'settings/templates/'
                    ,template          = 'template_model_example.model.lkml'
                    ,outFileName      = tenant + '_analytics.model'
                    ,outFileExtension = 'lkml'
                    ,outFileWritePath = git.absoluteOutputPath
            ) 
            w.bindTemplate()
            w.writeFile(overWriteExisting=True)


    #This will push the changes from your local repo to the remote in GitHub
    git.add().commit().pushRemote()
    # Here is where you would hit the deply URL of your project to have Looker pull from the remote/github
    #requests.get('https://company.looker.com/webhooks/projects/project_name/deploy')

    ### API CALL ###
    #Initialize the Looker API Class with the data in our config file (which is stored in a neighboring file 'config')
# import lib.api as foo
# x = foo.lookerAPIClient() 

# # print(x)

# look_params = {'connection':'snowflake_test', 'sql':'select * from fruit_basket'}

# print(x.post('sql_queries', 'snowflake','select test'))