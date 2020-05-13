import json
import urllib.request
from bs4 import BeautifulSoup
import time
import sqlite3
import cet_bus
from bus_history import BusHistory
from cet_bus.haversine import haversine
from cet_bus.geo import Point
from tracker import TransitSystemTracker

c = None

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
  return json_obj

class Route:
  def __init__(self, **kwargs):
    self.start = kwargs['start']
    self.end = kwargs['end']

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

# TODO: Special-case route 3225 which has no start/end data
routes =\
  {
    '290': Route(start=10084, end=16173),
    '292': Route(start=16173, end=2456764),
    '293': Route(start=2456762, end=2328349),
    '710': Route(start=2456761, end=21004),
    '711': Route(start=2456761, end=20970),
    '712': Route(start=2456765, end=20896),
    '713': Route(start=2456765, end=835820),
    '714': Route(start=2456765, end=805200),
    '715': Route(start=2456761, end=805200),
    '716': Route(start=2456762, end=2319861),
    '3136': Route(start=2456761, end=805200),
  }

def log():
  global c
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

  stops = None
  stops_info = {}

  for route_id in route_shapes:
    stops = stops_on_route(route_id)
    print(f'stops: {route_id}')
    stops_info[route_id] = stop_info_on_route(route_id)
    print(f'stops_info: {route_id}')

  transit = TransitSystemTracker(buses, stops_info, routes)
  while True:
    transit.update()
    time.sleep(1)
