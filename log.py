import json
import urllib.request
from bs4 import BeautifulSoup
import time
import sqlite3
import cet_bus
from bus_history import BusHistory

conn = sqlite3.connect('test.db')
c = conn.cursor()

c.execute('''
  create table if not exists buslog (
    bus char(32) not null,
    lat char(32) not null,
    lon char(32) not null,
    heading char(8) not null,
    speed char(8) not null,
    received datetime,
    route char(16) not null default '',
    stopid char(16) not null default '',
    primary key(bus, received)
  );
''')

def route_paths(route_id):
  paths = []
  for key, path in shapes.items():
    shape_id = key[0]
    route_id = key[1]
    paths.append(path)
  return paths

def passed_stops(route, hist):
  res = []
  for stop in stops:
    if cet_bus.passes(hist, stop, route):
      res.append(stop)

histories = {}
routes = {}
stops = []

with open('shape.json') as shape_file:
  with open('trips.json') as trips_file:
    shape_json = json.loads(shape_file.read())
    trips_json = json.loads(trips_file.read())
    shapes = cet_bus.enumerate_shapes(trips_json, shape_json)
    print('loaded shapes: ', shapes)

with open('stops.json') as stops_file:
  stops_json = json.loads(stops_file.read())
  for stop_json in stops_json:
    stops.append(cet_bus.Point(float(stop_json['stop_lat']), float(stop_json['stop_lon'])))

# Take a map of bus ids to histories and return a map of bus ids to most likely routes
def guess_routes(histories):
  result = {}
  for busid, history in histories.items():
    histo = cet_bus.route_histo(shapes, history.history)
    if histo:
      route_id = min(histo, key=lambda x: x[1])[0][1]
      print('guess_route: ', route_id)
      result[busid] = route_id
    else:
      result[busid] = None
  return result

while True:
  req = urllib.request.urlopen('http://ridecenter.org:7016')
  html = req.read()
  soup = BeautifulSoup(html, 'html.parser').body.string
  bus_json = json.loads(soup)
  for bus in bus_json:
    vals = [
      bus['busNumber'],
      bus['latitude'],
      bus['longitude'],
      bus['heading'],
      bus['speed'],
      bus['received']
    ]
    stmt = '''
      insert or ignore into buslog (bus,lat,lon,heading,speed,received) values (
        ?,
        ?,
        ?,
        ?,
        ?,
        ?
      );
    '''
    # c.execute(stmt, vals)
    if bus['busNumber'] in histories:
      print(f'bus: {bus["busNumber"]}')
      point = cet_bus.Point(
        float(bus['latitude']),
        float(bus['longitude'])
      )
      hist = histories[bus['busNumber']]
      hist.push(point)
      print(f'hist is {hist}')
      route_id = routes[bus['busNumber']]
      for path in route_paths(route_id):
        print(passed_stops(path, hist.get()))
    else:
      print(f'new bus: {bus["busNumber"]}')
      histories[bus['busNumber']] = BusHistory(3)
    routes = guess_routes(histories)
  print(histories)
  conn.commit()
  time.sleep(10)
