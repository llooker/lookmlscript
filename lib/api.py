import requests, logging, json
import urllib
import configparser as ConfigParser
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('settings/settings.ini')

class lookerAPIClient:
    def __init__(self 
            ,host       = config.get('api','host') 
            ,client_id  = config.get('api','client_id')
            ,secret     = config.get('api','secret')
            ,port       = config.get('api','port')
            ,version    = config.get('api','version')
            ):
        self.client_id  = client_id
        self.secret     = secret
        self.host           = host
        self.version        = version
        self.uri_stub       = '/api/{0}/'.format(self.version)
        self.uri_full       = ''.join([host, ':', port, self.uri_stub])
        self.login()

    def login(self):
        response = requests.post(self.uri_full + 'login', params={'client_id': self.client_id, 'client_secret': self.secret})
        self.access_token = response.json()['access_token']
        self.auth_headers = {
                'Authorization' : 'token ' + self.access_token,
                }

    def post(self, call='', json_payload=None):
        response = requests.post(self.uri_full + call, headers=self.auth_headers, json=json_payload)
        return response

    def get(self, call=''):
        response = requests.get(self.uri_full + call, headers=self.auth_headers)
        return response

    def get_columns(self, limit=100000, 
                                    fields=
                                    ["columns.table_schema",
                                    "columns.table_name",
                                    "columns.column_name",
                                    "columns.data_type"],
                                    filters={
                                        "columns.table_schema":""
                                        ,"columns.table_name":""
                                    }
                                    ):
                optional_arguments = '&' + 'limit=' + str(limit)
                query_config = {
                                "fields": [
                                    *fields
                                ],
                                "filters": {
                                        **filters
                                },
                                "model": config.get('api', 'information_schema_model'),
                                "view": config.get('api', 'explore')
                                }
                return self.post(call='queries/run/json?force_production=true' + optional_arguments, json_payload=query_config)