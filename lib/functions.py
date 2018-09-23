import re

def snakeCase(string):
    str1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', str1).lower()


def splice(*args):
    return ''.join([*args])


def removeSpace(string):  # removing special character / [|]<>,.?}{+=~!$%^&*()-
    return re.sub('(\s|/|\[|\]|\||\,|<|>|\.|\?|\{|\}|#|=|~|!|\+|\$|\%|\^|\&|\*|\(|\)|\-|\:)+', r'', string)


def lookCase(string):
    return removeSpace(snakeCase(string))


def stripID(identifier):
    if identifier.startswith('includes'):
        return '_'.join(identifier.split('_')[:-1])
    elif identifier.startswith('links'):
        return '_'.join(identifier.split('_')[:-1])
    elif identifier.startswith('filters'):
        return '_'.join(identifier.split('_')[:-1])
    elif identifier.startswith('bind_filters'):
        return '_'.join(identifier.split('_')[:-1])
        #splits by underbar, then removes the final piece and reassmebbles
    else:
        return identifier