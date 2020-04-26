import json
import urllib.request
from bs4 import BeautifulSoup
import time
import sqlite3
import cet_bus
from bus_history import BusHistory
from cet_bus.haversine import haversine
from cet_bus.geo import Point

class BusTracker:
  def __init__(self, stops):
    self.latest_position = None
    self.latest_stops = set()
    self.stops = stops

  def update(self, new_bus):
    current_stops = set()
    for stop in self.stops:
      stop_pos = Point(float(stop['stop_lat']), float(stop['stop_lon']))
      bus_pos = Point(float(new_bus['latitude']), float(new_bus['longitude']))
      # 4 meters is about 10 feet
      if haversine(stop_pos, bus_pos) < 4:
        current_stops.add((stop_pos.x, stop_pos.y))
    self.new_stops = self.latest_stops - current_stops
    self.latest_stops = current_stops
    self.latest_position = (new_bus['latitude'], new_bus['longitude'])

class TransitSystemTracker:
  def __init__(self, get_bus_data, stops_info):
    self.trackers = {}
    self.get_bus_data = get_bus_data
    self.stops_info = stops_info

  def update(self):
    bus_info = self.get_bus_data()
    print('***')
    print(bus_info)
    for bus in bus_info:
      route_id = bus['Route']
      stops_for_bus = self.stops_info[route_id]
      if route_id not in self.trackers:
        self.trackers[route_id] = BusTracker(stops_for_bus)
      self.trackers[route_id].update(bus)
      news = self.trackers[route_id].new_stops
      if len(news):
        print(news)
      else:
        print(f'no new stops on {route_id}')
