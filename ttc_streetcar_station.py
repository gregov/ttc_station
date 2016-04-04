import os
import logging
from flask import Flask, Response, send_from_directory
from lib.nextbus import getPrediction, getRouteConfig
from lib.svg_drawer import draw_groups


def next_vehicles(stop_id):
    res = {}
    destinations = getPrediction(stop_id)
    for idx, destination in enumerate(destinations):
        res[destination] = []
        for next_vehicle in destinations[destination]:
            res[destination].append(next_vehicle)

    logging.debug("Next vehicles: {}".format(res))
    return res

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
    return """<html>
                <body>

                    <h1> <img style="width:100px" src="res/TTC.svg"/> Next TTC streetcars</h1>
                    <h2>Steetcar routes</h2>
                    <ul>
                    <li><a href="/route/501"> 501 Queen</a>
                    <li><a href="/route/502"> 502 Downtowner</a>
                    <li><a href="/route/503"> 503 Kingston Rd</a>
                    <li><a href="/route/504"> 504 King</a>
                    <li><a href="/route/505"> 505 Dundas</a>
                    <li><a href="/route/506"> 506 Carlton</a>
                    <li><a href="/route/508"> 508 Lake Shore</a>
                    <li><a href="/route/509"> 509 Harbourfront</a>
                    <li><a href="/route/510"> 510 Spadina Accessible</a>
                    <li><a href="/route/511"> 511 Bathurst</a>
                    <li><a href="/route/512"> 512 St Clair</a>
                    </ul>
                    <h2>Night Streetcar Routes</h2>
                    <ul>
                    <li><a href="/route/301"> 301 Queen</a>
                    <li><a href="/route/304"> 304 King</a>
                    <li><a href="/route/306"> 306 Carlton</a>
                    <li><a href="/route/317"> 317 Spadina
                    </ul>
                </body>
              </html>"""


@app.route('/next_<int:stop_id>.svg')
def generate_svg(stop_id):
    return Response(draw_groups(next_vehicles(stop_id), ['red', 'blue', 'green']), mimetype="image/svg+xml")


@app.route('/route/<int:route_id>')
def get_route_config(route_id):
    route = getRouteConfig(route_id)
    stops = []
    for stop in route['stops']:
        stops.append("""Stop #{id}: <a href="/stop/{id}">{name}</a>""".format(id=stop['id'], name=stop['name']))

    return """<html>
                <body>
                    <h1> All Stops for route {}</h1>
                    {}
                </body>
              </html>""".format(route['name'], '<br />'.join(stops))


@app.route('/stop/<int:stop_id>')
def get_stop(stop_id):
    return """<html>
                <head><meta http-equiv="refresh" content="15    "></head>
                <body>
                    <h1> Next TTC streetcars for stop {stop_id}</h1>
                    <img style="width:40%" src="/next_{stop_id}.svg"/>
                </body>
              </html>""".format(stop_id=stop_id)


@app.route('/res/<path:path>')
def send_ressource(path):
    return send_from_directory('res', path)

if __name__ == '__main__':
    app.run()
