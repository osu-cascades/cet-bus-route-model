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
for t in range(20):
  x_disp_1 = math.sin(t*0.31416) / 10000
  y_disp_1 = math.cos(t*0.31416) / 10000
  x_disp_2 = math.sin((t+1)*0.31416) / 10000
  y_disp_2 = math.cos((t+1)*0.31416) / 10000
  bus_1 = { 'latitude': 40.0 + x_disp_1, 'longitude': 40.0 + y_disp_1, 'Route': '1' }
  bus_2 = { 'latitude': 45.0 + x_disp_2, 'longitude': 45.0 + y_disp_2, 'Route': '2' }
  fake_bus_data.append([ bus_1, bus_2 ])

# Simulate 3 stops on each of the same circles
stops_info = { '1': [], '2': [] }
for t in range(3):
  x_disp_1 = math.sin(t*2.0944) / 10000
  y_disp_1 = math.cos(t*2.0944) / 10000
  x_disp_2 = math.sin((t+1)*2.0944) / 10000
  y_disp_2 = math.cos((t+1)*2.0944) / 10000
  stop_1 = { 'stop_lat': 40.0 + x_disp_1, 'stop_lon': 40.0 + y_disp_1, 'direction_id': 0 }
  stop_2 = { 'stop_lat': 45.0 + x_disp_2, 'stop_lon': 45.0 + y_disp_2, 'direction_id': 1 }
  stops_info['1'].append(stop_1)
  stops_info['2'].append(stop_2)

i = 0
def get_fake_bus_data():
  global i
  res = fake_bus_data[i]
  i += 1
  i %= 20
  return res

transit = TransitSystemTracker(get_fake_bus_data, stops_info)
while True:
  transit.update()
  time.sleep(1)
