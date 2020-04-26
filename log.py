import json
import urllib.request
from bs4 import BeautifulSoup
import time
import sqlite3
import cet_bus
from bus_history import BusHistory
from cet_bus.haversine import haversine
from cet_bus.geo import Point

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

route_shapes = {
  '290': ['p_30', 'p_31', 'p_746', 'p_747', 'p_748'],
  '291': ['p_750','p_745','p_352','p_353'],
  '292': ['p_749','p_1116'],
  '293': ['p_1113','p_1112','p_744792','p_1667','p_1668'],
  '3136': ['p_180304','p_176598'],
  '3138': ['p_1105','p_176543'],
  '4695': ['p_745174'],
  '5917': ['p_1117','p_176608'],
  '382': ['p_751','p_753','p_176606','p_176607'],
  '710': ['p_1109','p_1124'],
  '711': ['p_1106','p_1123'],
  '712': ['p_1108','p_176539'],
  '713': ['p_1121','p_8009'],
  '714': ['p_1114','p_176595'],
  '715': ['p_1110','p_176596'],
  '716': ['p_177368','p_177368'],
  '740': ['p_744877'],
  '3225': ['p_180576','p_9617','p_180573','p_180574','p_111380']
}

class BusTracker:
  def __init__(self, shapes, stops):
    self.shapes = shapes
    self.stops = stops
    self.histories = {}
    self.route_paths = {}
    self.routes = {}
    self.path_stops = {}
    self.set_path_stops()
    self.route_short_name_to_route_id = {}
    self.index_route_short_names()

  def index_route_short_names(self):
    rows = c.execute('select route_id, route_short_name from routes')
    for row in rows:
      try:
        self.route_short_name_to_route_id[int(row[1])] = row[0]
      except ValueError:
        pass # Some routes do not have a short name

  def get_stops_for_shape(self, shape_id):
    stops = c.execute('''
      select distinct stop_lat, stop_lon, s.stop_id from
        stop_times st inner join stops s
          on st.stop_id = s.stop_id
      where trip_id = (
        select (trip_id) from trips where shape_id = ?
      )
    ''',
      (shape_id, )
    )
    result = []
    for stop in stops:
      print(shape_id, " => ", cet_bus.Point(stop[0], stop[1]))
      result.append(cet_bus.Point(float(stop[0]), float(stop[1])))
    return result

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
      try:
        route_id = int(self.routes[number])
      except:
        return # Bus is not on a route, so we don't care about it
      try:
        point = cet_bus.Point(
          float(bus_json['latitude']),
          float(bus_json['longitude'])
        )
      except:
        return
      hist = self.histories[number]
      hist.push(point)
      route_paths = self.get_route_paths(route_id)
      for path_id, path in route_paths:
        passed = self.passed_stops(path_id, path, hist.get())
        if passed:
          print(f'bus {number} just passed stops {passed}')
    else:
      print(f'new bus: {number}')
      self.histories[number] = BusHistory(3)

  # Take a map of bus ids to histories and return a map of bus ids to most likely routes
  def guess_routes(self, known_routes):
    result = {}
    for busid, history in self.histories.items():
      if busid in known_routes:
        result[busid] = known_routes[busid]
      else:
        histo = cet_bus.route_histo(self.shapes, history.history)
        if histo:
          route_id = min(histo, key=lambda x: x[1])[0][1]
          result[busid] = route_id
        else:
          result[busid] = None
      print(f'guess_route: bus {busid} is on {result[busid]}')
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

def get_known_routes(tracker):
  known_routes = {}
  req = urllib.request.urlopen('http://ridecenter.org:7017/list')
  list_json = req.read()
  buses = json.loads(list_json)
  for bus in buses:
    short_name = bus['Route']
    route_id = tracker.route_short_name_to_route_id[int(short_name)]
    known_routes[bus['bus']] = route_id
  return known_routes

def process_stream(tracker):
  while True:
    req = urllib.request.urlopen('http://ridecenter.org:7016')
    html = req.read()
    soup = BeautifulSoup(html, 'html.parser').body.string
    bus_json = json.loads(soup)
    for bus in bus_json:
      tracker.update_histories(bus)
    known_routes = get_known_routes(tracker)
    tracker.guess_routes(known_routes)
    conn.commit()
    time.sleep(10)

def stops_on_route(route_id):
  stmt = '''
    select distinct s.stop_id, stop_lat, stop_lon, stop_name from (
      trips t inner join stop_times st on t.trip_id = st.trip_id inner join stops s on s.stop_id = st.stop_id
    ) where route_id = ?;
  '''
  stops = c.execute(stmt, (route_id,))
  json_obj = []
  for stop in stops:
    json_obj.append({
      'stop_id': stop[0],
      'stop_lat': stop[1],
      'stop_lon': stop[2],
      'stop_name': stop[3]
    })
  return json_obj

def stop_info_on_route(route_id):
  stops = c.execute('''
    select stop_lat,stop_lon,trips.direction_id, stop_sequence,departure_time, trips.route_id, stops.stop_id, trips.trip_headsign, stops.stop_name, trips.trip_id
    from calendar
    join trips on trips.service_id=calendar.service_id
    join routes on trips.route_id=routes.route_id
    join stop_times on trips.trip_id=stop_times.trip_id
    join stops on stop_times.stop_id=stops.stop_id
    where trips.route_id=?
    order by trips.service_id,departure_time,direction_id,cast(shape_dist_traveled as real)
    limit 100000000;
  ''', (route_id, ))
  json_obj = []
  for stop in stops:
    json_obj.append({
      'stop_lat': stop[0],
      'stop_lon': stop[1],
      'direction_id': stop[2],
      'stop_sequence': stop[3],
      'departure_time': stop[4],
      'route_id': stop[5],
      'stop_id': stop[6],
      'trip_headsign': stop[7],
      'stop_name': stop[8],
      'trip_id': stop[9],
    })
  return json_obj

def buses():
  handle = urllib.request.urlopen('http://ridecenter.org:7017/list')
  json_obj = json.loads(handle.read().decode('utf8'))
  routes = c.execute('''
    select route_short_name, route_id from routes;
  ''')
  route_map = {}
  for route in routes:
    try:
      int_id = int(route[0])
      route_map[int_id] = int(route[1])
    except:
      route_map[route[0]] = int(route[1])
  for bus in json_obj:
    try:
      int_id = int(bus['Route'])
      bus['Route'] = route_map[int_id]
    except:
      bus['Route'] = route_map[bus['Route']]
  return json.dumps(json_obj),

stops = None
stops_info = {}

for route_id in route_shapes:
  stops = stops_on_route(route_id)
  print(f'stops: {route_id}')
  stops_info[route_id] = stop_info_on_route(route_id)
  print(f'stops_info: {route_id}')
print(buses())

class BusTracker:
  def __init__(self, stops):
    self.latest_position = None
    self.latest_stops = set()
    self.stops = stops

  def update(self, new_bus):
    current_stops = set()
    for stop in self.stops:
      # 4 meters is about 10 feet
      stop_pos = Point(float(stop['stop_lat']), float(stop['stop_lon']))
      bus_pos = Point(float(new_bus['latitude']), float(new_bus['longitude']))
      if haversine(stop_pos, bus_pos) < 4:
        current_stops.add(stop)
    self.new_stops = self.latest_stops - current_stops
    self.latest_stops = current_stops
    self.latest_position = (new_bus['latitude'], new_bus['longitude'])

trackers = {}

fake_bus_data =\
  [ { 'busNumber': '1', 'latitude': '40', 'longitude': '40', 'Route': '710' },
    { 'busNumber': '2', 'latitude': '40.1', 'longitude': '40.1', 'Route': '711' }
  ]

def update():
  #bus_info = buses()
  bus_info = fake_bus_data
  print('***')
  print(bus_info)
  for bus in bus_info:
    route_id = bus['Route']
    stops_for_bus = stops_info[route_id]
    if route_id not in trackers:
      trackers[route_id] = BusTracker(stops_for_bus)
    trackers[route_id].update(bus)
    news = trackers[route_id].new_stops
    if len(news):
      print(news)
    else:
      print(f'no new stops on {route_id}')

while True:
  update()
  time.sleep(1)
