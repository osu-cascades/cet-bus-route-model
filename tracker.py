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
  # Start is the stop id at which the bus restarts its route
  # End is the stop id at which the bus turns around and flips its direction id
  def __init__(self, stops, start, end):
    self.latest_position = None
    self.latest_stops = set()
    self.stops = stops
    self.start = start
    self.end = end
    self.direction_id = 0

  def update(self, new_bus):
    print(f"updating {new_bus['bus']}")
    current_stops = set()
    print(len(self.stops))
    for stop in self.stops:
      stop_pos = Point(float(stop['stop_lat']), float(stop['stop_lon']))
      bus_pos = Point(float(new_bus['latitude']), float(new_bus['longitude']))
      # 4 meters is about 10 feet
      if haversine(stop_pos, bus_pos) < 50:
        print(f"At stop {stop['stop_id']} (bus id: {new_bus['bus']})")
        if stop['stop_id'] == self.start:
          self.direction_id = 0
        if stop['stop_id'] == self.end:
          self.direction_id = 1
        if self.direction_id == int(stop['direction_id']):
          current_stops.add((stop_pos.x, stop_pos.y, stop['stop_id']))
    self.new_stops = self.latest_stops - current_stops
    self.latest_stops = current_stops
    self.latest_position = (new_bus['latitude'], new_bus['longitude'])

class TransitSystemTracker:
  def __init__(self, get_bus_data, stops_info, routes):
    self.trackers = {}
    self.get_bus_data = get_bus_data
    self.stops_info = stops_info
    self.routes = routes

  def update(self):
    bus_info = self.get_bus_data()
    print('***')
    print([bus['Route'] for bus in bus_info])
    for bus in bus_info:
      bus_id = str(bus['bus'])
      route_id = str(bus['Route'])
      stops_for_bus = self.stops_info[route_id]
      try:
        start = self.routes[route_id].start
        end = self.routes[route_id].end
      except:
        print(f'No start/end data for route {route_id}; skipping')
        continue
      self.trackers[bus_id] = BusTracker(stops_for_bus, start, end)
      self.trackers[bus_id].update(bus)
      news = self.trackers[bus_id].new_stops
      print(self.trackers[bus_id].latest_stops)
      if len(news):
        print(news)
      else:
        print(f'no new stops for bus #{bus_id} on route #{route_id}')
