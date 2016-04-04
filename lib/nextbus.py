import requests
import json
import logging
import xmltodict

# API section
AGENCY_TAG = 'ttc'
FAVORITE_ROUTES = (510,)
FAVORITE_STOPS = (15332, 15333)


class NextBusApi:
    def __init__(self, base_url=None, agency='ttc'):
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = 'http://webservices.nextbus.com/service/publicXMLFeed'
        self.agency = agency

    def call(self, method, **kwargs):
        url_template = self.base_url + '?command={cmd}&a={agency_tag}&t=0'
        url = url_template.format(cmd=method, agency_tag=self.agency)
        for arg in kwargs:
            if arg == 'route_id':
                url += '&r={}'.format(kwargs['route_id'])
            if arg == 'stop_id':
                url += '&stopId={}'.format(kwargs['stop_id'])
        logging.debug('Request: {}'.format(url))
        response = requests.get(url)
        parsed_response = xmltodict.parse(response.text)
        logging.debug('Response: {}'.format(self.format(parsed_response)))
        return parsed_response

    def format(self, raw_dict):
        return json.dumps(raw_dict, indent=4)

my_api = NextBusApi(agency=AGENCY_TAG)


def getRouteConfig(route_id):
    res = my_api.call('routeConfig', route_id=route_id)
    logging.debug(my_api.format(res))
    stops = []
    for tmp in res['body']['route']['stop']:
        if '@stopId' in tmp:
            stops.append({
                    'name': tmp['@title'],
                    'id': tmp['@stopId']
                })
    result = {'name': res['body']['route']['@title'],
              'stops': stops
              }
    return result


def getVehicles(route_id):
    output = ""
    result = my_api.call('vehicleLocations', route_id=route_id)
    for vehicle in result['body']['vehicle']:
        output += vehicle['@id'], vehicle['@lat'], vehicle['@lon'], vehicle['@heading']
    return output


def getPrediction(stop_id):
    result = my_api.call('predictions', stop_id=stop_id)
    res = {}
    print result
    for predictions in result['body']['predictions']:
        if 'direction' in predictions:
            if 'prediction' in predictions['direction']:
                # accumulator by destination
                temp = []
                for next_vehicle in predictions['direction']['prediction']:
                    temp.append(next_vehicle['@minutes'])
                res[predictions['direction']['@title']] = temp

    return res


def getMessages(route_id):
    return my_api.call('messages', route_id=route_id)


def getSchedule(route_id):
    return my_api.call('schedule', route_id=route_id)


def get_route(routes):
    for route_id in routes:
        print "Streetcar #{}".format(route_id)
        print getRouteConfig(route_id)
        print getVehicles(route_id)
        vehicle_id = 4232
        print getMessages(vehicle_id)
        print getSchedule(vehicle_id)
