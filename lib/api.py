import  requests
import configparser as ConfigParser
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('settings/settings.ini')

class lookerAPIClient:
    def __init__(
                 self
                ,api_host = config.get('api', 'api_host')
                ,api_client_id   = config.get('api', 'api_client_id')
                ,api_secret      = config.get('api', 'api_secret')
                ,api_port        = config.get('api', 'api_port')):
        auth_request_payload = {'client_id': api_client_id, 'client_secret': api_secret}
        self.host = api_host
        self.uri_stub = '/api/3.0/'
        self.uri_full = ''.join([api_host, ':', api_port, self.uri_stub])
        response = requests.post(self.uri_full + 'login', params=auth_request_payload)
        authData = response.json()
        self.access_token = authData['access_token']
        self.auth_headers = {
                'Authorization' : 'token ' + self.access_token,
                }

    def get(self, call=''):
        response = requests.get(self.uri_full + call, headers=self.auth_headers)
        return response.json()

    def post(self, call='', json_payload=None):
        response = requests.post(self.uri_full + call, headers=self.auth_headers, data=json_payload)
        return response

    # def post(self, **kwargs):
    #     payload = {'connection':connection, 'sql':sql}
    #     response = requests.post(self.uri_full, data=payload, headers=self.auth_headers)
    #     return response.json()

    def getLooks(self):
        return self.get('looks')

    def runLook(self, look, limit=100):
        optional_arguments = '?' + 'limit=' + str(limit)
        return self.get('/'.join(['looks',look,'run','json'])+optional_arguments)

    def getlookinfo(self, look):
        return self.get('look')

    def getdashboardinfo(self, dashboard_id):
        return self.get('/'.join(['dashboards',dashboard_id]))

    def createSQLQuery(self,slug):
        return self.post('sql_queries', slug=slug)

    def connection_name(self,fields):
        return self.get(''.join(['/connections','?fields=',fields]))

    def lookmlmodel_info(self,modelname):
        return self.get('/'.join(['lookml_models',modelname]))

    def get_columns(self, limit=100000, schema="", table_name=""):
            optional_arguments = '&' + 'limit=' + str(limit)
            query_config = {
                            "fields": [
                                "columns.table_schema",
                                "columns.table_name",
                                "columns.column_name",
                                "columns.data_type"
                            ],
                            "filters": {
                                     "columns.table_schema":schema
                                    ,"columns.table_name": table_name
                            },
                            "model": config.get('api', 'information_schema_model'),
                            "view": config.get('api', 'explore')
                            }
            
            # print(config.get('api', 'information_schema_model'))
            return self.post(call='queries/run/json?force_production=true' + optional_arguments, json_payload=query_config)
        