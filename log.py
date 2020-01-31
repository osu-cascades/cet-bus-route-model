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

class BusTracker:
  def __init__(self, shapes, stops):
    self.shapes = shapes
    self.stops = stops
    self.histories = {}
    self.route_paths = {}
    self.routes = {}
    self.path_stops = {}
    self.set_path_stops()

  def get_stops_for_shape(self, shape_id):
    stops = c.execute('''
      select (stop_id) from stop_times where trip_id = (
        select (trip_id) from trips where shape_id = ?
      )
    ''',
      (shape_id, )
    )
    for stop in stops:
      print(shape_id, " => ", stop[0])
    return stops

  def set_path_stops(self):
    for key, path in self.shapes.items():
      print(f'assigning stops to path {key}')
      self.path_stops[key[0]] = self.get_stops_for_shape(key[0])

  def get_route_paths(self, route_id):
    if route_id not in self.route_paths:
      paths = []
      for key, path in self.shapes.items():
        shape_id = key[0]
        if route_id == key[1]:
          paths.append( (shape_id, path) )
      self.route_paths[route_id] = paths
    return self.route_paths[route_id]

  def passed_stops(self, path_id, path, hist):
    res = []
    for stop in self.path_stops[path_id]:
      if cet_bus.passes(hist, stop, path):
        res.append(stop)
    return res

  def update_histories(self, bus_json):
    number = bus_json['busNumber']
    if number in self.histories:
      print(f'updating bus: {number}')
      try:
        point = cet_bus.Point(
          float(bus_json['latitude']),
          float(bus_json['longitude'])
        )
      except:
        print('invalid bus record for {number}')
        return
      hist = self.histories[number]
      hist.push(point)
      print(f'hist is {hist.history}')
      route_id = self.routes[number]
      for path_id, path in thingy.get_route_paths(route_id):
        passed = self.passed_stops(path_id, path, hist.get())
        if passed:
          print(f'bus {number} just passed stops {passed}')
    else:
      print(f'new bus: {number}')
      self.histories[number] = BusHistory(3)

  # Take a map of bus ids to histories and return a map of bus ids to most likely routes
  def guess_routes(self):
    result = {}
    for busid, history in self.histories.items():
      histo = cet_bus.route_histo(self.shapes, history.history)
      if histo:
        route_id = min(histo, key=lambda x: x[1])[0][1]
        print(f'guess_route: bus {busid} is on {route_id}')
        result[busid] = route_id
      else:
        result[busid] = None
    self.routes = result

def initialize():
  stops = []
  shapes = None
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
  return BusTracker(shapes, stops)

def insert_bus_observation(bus):
  vals = [
    bus['busNumber'],
    bus['latitude'],
    bus['longitude'],
    bus['heading'],
    bus['speed'],
    bus['received']
  ]
  stmt = '''
    insert or ignore into buslog (bus,lat,lon,heading,speed,received) values
      (?, ?, ?, ?, ?, ?);
  '''
  c.execute(stmt, vals)

def process_stream(thingy):
  while True:
    req = urllib.request.urlopen('http://ridecenter.org:7016')
    html = req.read()
    soup = BeautifulSoup(html, 'html.parser').body.string
    bus_json = json.loads(soup)
    for bus in bus_json:
      thingy.update_histories(bus)
    thingy.guess_routes()
    print(thingy.histories)
    conn.commit()
    time.sleep(10)

thingy = initialize()
process_stream(thingy)
