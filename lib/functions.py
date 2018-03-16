import re

"""
Author:			Russell Garner
Created Date:	2017
Description:	

Changes:
Author			Date 			Description
------------------------------------------------------
BoRam Hong		2018.01.11		Added lookCase to remove spaces
BoRam Hong 		2018.01.12		Removing special characters
"""


def snakeCase(string):
    str1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', str1).lower()


def splice(*args):
    return ''.join([*args])


def removeSpace(string):  # removing special character / [|]<>,.?}{+=~!$%^&*()-
    return re.sub('(\s|/|\[|\]|\||\,|<|>|\.|\?|\{|\}|#|=|~|!|\+|\$|\%|\^|\&|\*|\(|\)|\-|\:)+', r'', string)


def lookCase(string):
    return removeSpace(snakeCase(string))
