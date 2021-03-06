from flask import Flask, jsonify
import threading
import time
from log import log

app = Flask(__name__)

transit_state = { 'value': None }

def lat_long(bus_tracker):
  try:
    return bus_tracker.latest_position[0], bus_tracker.latest_position[1]
  except TypeError:
    return None, None

def bus_positions():
  tracker = transit_state['value']
  res = {}
  for bus_id in tracker.trackers:
    bus_tracker = tracker.trackers[bus_id]
    lat, lon = lat_long(bus_tracker)
    res[bus_id] = {
      'route_id': bus_tracker.route_id,
      'lat': lat,
      'lon': lon }
  return res

def new_stops():
  tracker = transit_state['value']
  res = {}
  for bus_id in tracker.trackers:
    bus_tracker = tracker.trackers[bus_id]
    res[bus_id] = []
    bus_on_route = res[bus_id]
    for arr in bus_tracker.new_stops:
      bus_on_route.append({
        'route_id': bus_tracker.route_id,
        'lat': arr.lat,
        'lon': arr.lon,
        'stop_id': arr.stop_id })
  return res

def latest_stops():
  tracker = transit_state['value']
  res = {}
  for bus_id in tracker.trackers:
    bus_tracker = tracker.trackers[bus_id]
    res[bus_id] = []
    bus_on_route = res[bus_id]
    for arr in bus_tracker.latest_stops:
      bus_on_route.append({
        'route_id': bus_tracker.route_id,
        'lat': arr.lat,
        'lon': arr.lon,
        'stop_id': arr.stop_id })
  return res

@app.route('/')
def buses():
  response = jsonify({
    'bus_positions': bus_positions(),
    'new_stops': new_stops(),
    'latest_stops': latest_stops()
  })
  response.headers.add('Access-Control-Allow-Origin', '*')
  return response

def log_task():
  global transit_state
  log(transit_state)

t = threading.Thread(target=log_task)
t.start()
