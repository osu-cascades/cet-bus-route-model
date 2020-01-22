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

def passed_stops(route, hist):
  res = []
  for stop in hist:
    if passes(hist, stop, route):
      res.append(stop)

histories = {}
routes = {}

# Take a map of bus ids to histories and return a map of bus ids to most likely routes
def guess_routes(histories):
  pass

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
      point = cet_bus.geo.Point(bus['latitude'], bus['longitude'])
      hist = histories[bus['busNumber']]
      hist.push(point)
      print(f'hist is {hist}')
      print(passed_stops(route[bus['busNumber']], hist.get()))
    else:
      print(f'new bus: {bus["busNumber"]}')
      histories[bus['busNumber']] = BusHistory(3)
    routes = guess_routes(histories)
  print(histories)
  conn.commit()
  time.sleep(10)
