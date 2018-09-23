#!/usr/bin/env python3
# -- #!/usr/bin/env python
import lib.lookML as lookml
import lib.writer 
import lib.db as db
import lib.gitController
import logging
import os 
import lib.functions as f

import requests

d = db.database()

print(d)

# Instantiating a view with a name, adding dims and measures
# myView = lookml.View()
# myView.setName('View_1')
# myView.setSqlTableName('public.order_items')
# myView.addDimension('id')
# myView.addDimension('order_count')
# myView.addCountDistinct('id')
# myView.addCountDistinct('brand_new')
# myView.addField(identifier='new_Field')
# # myView.removeField('id')
# myView.setMessage('this is my commmented message')
# myView.setLabel('labelsetting')
# # myView.setExtensionRequired()
# generator = myView.getFields()


# print(myView)

# Instantiating a model NOT WORKING YET
# model_input = {
#     "connection":"test_connection",
#     "include":"*.view.lkml"
#             }
# myModel = lookml.Model(model_input)
# myModel.setName('test')
# myModel.include('myView')
# myModel.addExplore('new_explore')


# myExplore = lookml.Explore(view='test_view')
# myExplore.setViewName('test')

# myJoin = lookml.Join(_from='test_view')
# myJoin.setName('test_join')

# print(myModel)

# myView = lookml.View().createViewFromTable('''RPT.vwDimUserCustomField_1N2MAFRQNY''')