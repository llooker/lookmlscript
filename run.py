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
    git = lib.gitController.gitController(projectName='mylookerproject2', branch='master') #will create a folder in the output directory to contain the cloned project
    git.clone('git@github.com:russlooker/the_look_scripted.git') ## Your Existing lookml project
    infoSchema = lib.lookML.viewFactory(tablePattern='%')
    logging.info(infoSchema)
    airports = infoSchema.createView(table='airports',schema='flightstats')
    flights = infoSchema.createView(table='zipcodes',schema='flightstats')
    # ~order_items
    airports.addCountDistinct('county')
    airports.addCountDistinct('elevation')
    airports.setOutFilePath(git.absoluteOutputPath)
    flights.setOutFilePath(git.absoluteOutputPath)
    flight_stats = lib.lookML.Model('flightstats')
    flight_stats.setConnection("thelook")
    flight_stats.setOutFilePath(git.absoluteOutputPath)
    flight_stats.include('*.view.lkml')
    # flight_stats.include(airports)
    flights_explore = lib.lookML.Explore(flights)
    flight_stats.addExplore(flights_explore)
    flight_stats.writeFile(overWriteExisting=True)
    airports.writeFile(overWriteExisting=True)
    flights.writeFile(overWriteExisting=True)
    # if FIRST_RUN:
    #     tenants = ['tennat1','tennat2','tennat3']
    #     for tenant in tenants:
    #         templateContext = {
    #             "tenant": tenant,
    #             "additional_join_flag":True
    #             #,Hypothetical other variables you want to pass into the template renderer
    #         }
    #         w = lib.writer.templateProcessor(
    #                 contextVariables = templateContext
    #                 ,templatePath     = 'settings/templates/'
    #                 ,template          = 'template_model_example.model.lkml'
    #                 ,outFileName      = tenant + '_analytics.model'
    #                 ,outFileExtension = 'lkml'
    #                 ,outFileWritePath = git.absoluteOutputPath
    #         ) 
    #         w.bindTemplate()
    #         w.writeFile(overWriteExisting=True)


    #This will push the changes from your local repo to the remote in GitHub
    git.add().commit().pushRemote()
    # Here is where you would hit the deply URL of your project to have Looker pull from the remote/github
    requests.get('https://looker.russelljgarner.com/webhooks/projects/the_look_scripted/deploy')



# if __name__ == '__main__':
#     git = lib.gitController.gitController(projectName='mylookerproject1', branch='master') #will create a folder in the output directory to contain the cloned project
#     git.clone('git@github.com:russlooker/lookmlscript_test_project.git') ## Your Existing lookml project

#     myView  = lib.lookML.View() #Instantiate the view
#     myView.setSqlTableName('public.order_items') 
#     myView.setName('myViewName')
#     myView.addDimension('id')
#     myView.addDimension('value')
#     myView.addSum(myView['value'])
#     myView['value'].hide()

#     myView.addCountDistinct(myView['id'])
#     myView.setOutFilePath(git.absoluteOutputPath)
#     myView.writeFile(overWriteExisting=True)

#     if FIRST_RUN:
#         tenants = ['tennat1','tennat2','tennat3']
#         for tenant in tenants:
#             templateContext = {
#                 "tenant": tenant,
#                 "additional_join_flag":True
#                 #,Hypothetical other variables you want to pass into the template renderer
#             }
#             w = lib.writer.templateProcessor(
#                     contextVariables = templateContext
#                     ,templatePath     = 'settings/templates/'
#                     ,template          = 'template_model_example.model.lkml'
#                     ,outFileName      = tenant + '_analytics.model'
#                     ,outFileExtension = 'lkml'
#                     ,outFileWritePath = git.absoluteOutputPath
#             ) 
#             w.bindTemplate()
#             w.writeFile(overWriteExisting=True)


#     #This will push the changes from your local repo to the remote in GitHub
#     git.add().commit().pushRemote()
#     # Here is where you would hit the deply URL of your project to have Looker pull from the remote/github
#     #requests.get('https://company.looker.com/webhooks/projects/project_name/deploy')