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
import math

# Simulate buses moving in separate circles, each sampled at 20 points
fake_bus_data = []
for t in range(60):
  if t < 30:
    x = 0.0003 * t / 30
  else:
    x = 0.0003 - (0.0003 * (t - 30) / 30)
  bus_1 = { 'latitude': 40 + x, 'longitude': 40.0, 'Route': '1', 'bus': '1' }
  fake_bus_data.append([ bus_1 ])

route_1_stops = [40, 40.0001, 40.0002, 40.0003, 40.0002, 40.0001]

stops_info = { '1': [] }
for t, x in enumerate(route_1_stops):
  stop_1 = {
    'stop_lat': x,
    'stop_lon': 40.0,
    'direction_id': 0 if t < 3 else 1,
    'stop_id': t
  }
  stops_info['1'].append(stop_1)

print(fake_bus_data)
print(stops_info)

i = 0
def get_fake_bus_data():
  global i
  res = fake_bus_data[i]
  i += 1
  i %= 20
  return res

class Route:
  def __init__(self, **kwargs):
    self.start = kwargs['start']
    self.end = kwargs['end']

routes =\
  { '1': Route(start=0, end=3),
    '2': Route(start=0, end=-1)
  }

transit = TransitSystemTracker(get_fake_bus_data, stops_info, routes)

while True:
  transit.update()
  time.sleep(1)
