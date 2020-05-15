import json
import urllib.request
from bs4 import BeautifulSoup
import time
import sqlite3
import cet_bus
from cet_bus.haversine import haversine
from cet_bus.geo import Point

class BusTracker:
  # Start is the stop id at which the bus restarts its route
  # End is the stop id at which the bus turns around and flips its direction id
  def __init__(self, stops, route_id, start, end):
    self.latest_position = None
    self.latest_stops = set()
    self.stops = stops
    self.route_id = route_id
    self.start = start
    self.end = end
    self.direction_id = 0
    self.bus_stop_radius = 50
    self.new_stops = set()
    self.latest_stops = set()

  def update(self, new_bus):
    try:
      bus_pos = Point(float(new_bus['latitude']), float(new_bus['longitude']))
    except ValueError:
      # Empty lat/long
      return
    except KeyError:
      # No lat/long
      return
    current_stops = set()
    for stop in self.stops:
      stop_pos = Point(float(stop['stop_lat']), float(stop['stop_lon']))
      if haversine(stop_pos, bus_pos) < self.bus_stop_radius:
        if stop['stop_id'] == self.start:
          self.direction_id = 0
        if stop['stop_id'] == self.end:
          self.direction_id = 1
        if self.direction_id == int(stop['direction_id']):
          current_stops.add((stop_pos.x, stop_pos.y, stop['stop_id'], new_bus['received']))
    if self.latest_stops:
      self.new_stops = current_stops - self.latest_stops
    else:
      self.new_stops = set()
    self.latest_stops = set(current_stops)
    self.latest_position = (new_bus['latitude'], new_bus['longitude'])

class TransitSystemTracker:
  def __init__(self, get_bus_data, stops_info, routes, log_arrival, log_position):
    self.trackers = {}
    self.get_bus_data = get_bus_data
    self.stops_info = stops_info
    self.routes = routes
    self.log_arrival = log_arrival
    self.log_position = log_position

  def update(self):
    bus_info = self.get_bus_data()
    for bus in bus_info:
      bus_id = str(bus['bus'])
      route_id = str(bus['Route'])
      if bus_id not in self.trackers:
        self.add_bus_tracker(bus_id, route_id)
      elif self.trackers[bus_id] is not None:
        self.update_bus_route(bus_id, route_id)
        self.log_position(bus)
        self.trackers[bus_id].update(bus)
        news = self.trackers[bus_id].new_stops
        if len(news):
          print(f'arrival: {news}')
          for lat, lon, stop_id, received in news:
            self.log_arrival(bus_id, lat, lon, stop_id, received)


  def add_bus_tracker(self, bus_id, route_id):
    stops_for_bus = self.stops_info[route_id]
    try:
      start = self.routes[route_id].start
      end = self.routes[route_id].end
    except:
      print(f'No start/end data for route {route_id}; skipping')
      self.trackers[bus_id] = None
      return
    self.trackers[bus_id] = BusTracker(stops_for_bus, route_id, start, end)

  # Re-initialize the tracker for the given bus if the route changes
  def update_bus_route(self, bus_id, route_id):
    if self.trackers[bus_id].route_id != route_id:
      self.add_bus_tracker(bus_id, route_id)
