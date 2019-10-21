import json

class InvalidItemException(Exception):

    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class Database:

    def __init__(self, design):
        file = open('./databases/' + design + '.json', 'r')
        self.json_db = json.load(file)

    def get_data(self, target):
        try:
            #print(self.json_db)
            if target in self.json_db:
                return self.json_db[target]
            else:
                return None
        except KeyError:
            raise InvalidItemException(target + ' not found in database')
