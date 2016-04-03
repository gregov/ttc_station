import os
import requests
import xmltodict
import logging
from flask import Flask, Response

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
        logging.debug('Calling {}'.format(url))
        response = requests.get(url)
        return xmltodict.parse(response.text)

my_api = NextBusApi(agency=AGENCY_TAG)


def getRouteConfig(route_id):
    return my_api.call('routeConfig', route_id=route_id)


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
        print getMessages(vehicle_id)
        print getSchedule(vehicle_id)


# SVG Section

def render(template_file, content, output_file=None):
    with open(template_file, 'r') as f_template:
        output = f_template.read().format(**content)
        if output_file:
            with open(output_file, 'w') as f_output:
                f_output.write(output)
        else:
            return output


def dynamic_svg(stop_id):
        hands = []
        hand_template = """<g class="linearc" transform="rotate({angle}, 467, 230)">
                            <path stroke="{color}" stroke-width="4.0" stroke-linejoin="round" stroke-linecap="butt"
                                  d="m467.2651 230.3622l-2.2389526 -143.18402" fill-rule="evenodd"></path>
                            <path stroke="{color}" stroke-width="4.0" stroke-linecap="butt"
                                  d="m471.63226 87.07487l-6.889923 -18.046867l-6.322296 18.253464z"
                                  fill-rule="evenodd"></path>
                           </g>"""

        legend_template = """<text x="320" y="{legend_y}" style= "stroke: {color}; fill: #ffffff"
                             font-family="Arial" font-size="12">{text}</text>"""

        colors = ["#140000", "#CC0000"]
        legends = ''
        destinations = getPrediction(stop_id)
        for idx, destination in enumerate(destinations):
            text = "{}: {} min".format(destination, destinations[destination][0])
            legend_y = int(290 + 14 * idx)
            color = colors[idx]
            legends += legend_template.format(text=text, legend_y=legend_y, color=color)

            for next_vehicle in destinations[destination]:
                angle = int(next_vehicle) * 6
                print next_vehicle, angle
                hands.append(hand_template.format(angle=angle, color=color))

        data = {'stop_id': stop_id,
                'legends': legends,
                'hands': "\n".join(hands)
                }

        template_file = os.path.join(os.path.dirname(__file__) + 'next_streetcar.svg')
        # output_file = os.path.join(os.path.dirname(__file__) + "next_{}.svg".format(stop_id))
        return render(template_file, data)

# Web corner
app = Flask(__name__)
# filename=__name__ + '.log',

logging.basicConfig(level=10,
                    format=('%(asctime)s %(name)s@{}[%(process)d] '.format(os.getenv('HOSTNAME')) +
                            '%(levelname)-8s %(message)s' +
                            '    [in %(pathname)s:%(funcName)s:%(lineno)d]'),
                    datefmt='%m-%d %H:%M')


@app.route('/')
def index():
    stops = []
    for stop in FAVORITE_STOPS:
        stops.append("""<img style="width:40%" src="/next_{}.svg"/>""".format(stop))
    return """<html>
                <body>
                    <h1> Next TTC streetcars</h1>
                    {}
                </body>
              </html>""".format("\n".join(stops))


@app.route('/next_<int:stop_id>.svg')
def generate_svg(stop_id):
    return Response(dynamic_svg(stop_id), mimetype="image/svg+xml")


if __name__ == '__main__':
    app.run()
