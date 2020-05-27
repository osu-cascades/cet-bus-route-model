import json
import unittest

from geo import Point, Segment, Polyline
from bus_routes import *
from haversine import haversine

class TestBusRoutesMethods(unittest.TestCase):
  def test_enumate_shapes_has_correct_keys(self):
    trips = [
        {"shape_id": 0, "route_id": "route 1"},
        {"shape_id": 1, "route_id": "route 1"},
        {"shape_id": 2, "route_id": "route 2"}
      ]
    shapes = [
        {"shape_pt_lat": 0, "shape_pt_lon": 0, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 1, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 2, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 3, "shape_id": 0}
      ]
    shapes_map = enumerate_shapes(trips, shapes)

    self.assertIn((0, 'route 1'), shapes_map)
    self.assertNotIn((0, 'route 2'), shapes_map)

  def test_enumate_shapes_has_correct_values(self):
    trips = [
        {"shape_id": 0, "route_id": "route 1"},
        {"shape_id": 1, "route_id": "route 1"},
        {"shape_id": 2, "route_id": "route 2"}
      ]
    shapes = [
        {"shape_pt_lat": 0, "shape_pt_lon": 0, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 1, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 2, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 3, "shape_id": 0}
      ]
    shapes_map = enumerate_shapes(trips, shapes)

    polyline = Polyline([
      Point(0, 0),
      Point(0, 1),
      Point(0, 2),
      Point(0, 3)
    ])

    self.assertTrue(shapes_map[(0, 'route 1')] == polyline)

  def test_enumerate_shapes_fails_when_shape_has_many_routes(self):
    trips = [
        {"shape_id": 0, "route_id": "route 1"},
        {"shape_id": 0, "route_id": "route 2"}
      ]
    shapes = [
        {"shape_pt_lat": 0, "shape_pt_lon": 0, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 1, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 2, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 3, "shape_id": 0}
      ]
    with self.assertRaises(ValueError):
      enumerate_shapes(trips, shapes)

  def test_guess_route(self):
    trips_json = [
        {"shape_id": 0, "route_id": "route 1"},
        {"shape_id": 1, "route_id": "route 2"}
      ]
    shapes_json = [
        {"shape_pt_lat": 0, "shape_pt_lon": 0, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 1, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 2, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 3, "shape_id": 0},

        {"shape_pt_lat": 1, "shape_pt_lon": 0, "shape_id": 1},
        {"shape_pt_lat": 1, "shape_pt_lon": 1, "shape_id": 1},
        {"shape_pt_lat": 1, "shape_pt_lon": 2, "shape_id": 1},
        {"shape_pt_lat": 1, "shape_pt_lon": 3, "shape_id": 1}
      ]
    shapes = enumerate_shapes(trips_json, shapes_json)

    bus = {"latitude": 0.51, "longitude": 0}
    closest = guess_route(shapes, bus)
    self.assertEqual(closest[1], "route 2")

    bus = {"latitude": 0.49, "longitude": 0}
    closest = guess_route(shapes, bus)
    self.assertEqual(closest[1], "route 1")

  def test_route_histo(self):
    trips_json = [
        {"shape_id": 0, "route_id": "route 1"},
        {"shape_id": 1, "route_id": "route 2"}
      ]
    shapes_json = [
        {"shape_pt_lat": 0, "shape_pt_lon": 0, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 1, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 2, "shape_id": 0},
        {"shape_pt_lat": 0, "shape_pt_lon": 3, "shape_id": 0},

        {"shape_pt_lat": 0, "shape_pt_lon": 0, "shape_id": 1},
        {"shape_pt_lat": 0, "shape_pt_lon": 1, "shape_id": 1},
        {"shape_pt_lat": 0, "shape_pt_lon": 2, "shape_id": 1},
        {"shape_pt_lat": 1, "shape_pt_lon": 2, "shape_id": 1}
      ]
    shapes = enumerate_shapes(trips_json, shapes_json)

    bus_history = [
        Point(0, 0),
        Point(0, 1),
        Point(0, 2),
        Point(0, 3)
      ]
    histo = route_histo(shapes, bus_history)
    self.assertEqual(min(histo, key=lambda x: x[1])[0][1], "route 1")

    bus_history[3] = Point(1, 2)

    histo = route_histo(shapes, bus_history)
    self.assertEqual(min(histo, key=lambda x: x[1])[0][1], "route 2")

  def test_passes(self):
    route = Polyline([
      Point(0, 0),
      Point(0, 10)
    ])

    stop = Point(0, 5)

    # Buses can pass a stop going 'forward'
    bus_history = [ Point(0, 4), Point(0, 5), Point(0, 6) ]
    p = passes(bus_history, stop, route)
    self.assertTrue(p)

    # Buses can pass a stop going 'backward'
    bus_history = [ Point(0, 6), Point(0, 5), Point(0, 4) ]
    p = passes(bus_history, stop, route)
    self.assertTrue(p)

    # Not passing the stop should return false
    bus_history = [ Point(0, 4), Point(0, 3), Point(0, 2) ]
    p = passes(bus_history, stop, route)
    self.assertFalse(p)

    # Not moving at all should return false
    bus_history = [ Point(0, 6), Point(0, 6), Point(0, 6) ]
    p = passes(bus_history, stop, route)
    self.assertFalse(p)

    # Questionable edge case: should this count as passing the stop?
    bus_history = [ Point(0, 5), Point(0, 5), Point(0, 5) ]
    p = passes(bus_history, stop, route)
    self.assertFalse(p)

  def test_passes_with_loop(self):
    # Square route that loops back on itself at (0, 0)
    route = Polyline([
      Point(0, 0),
      Point(0, 1),
      Point(1, 1),
      Point(1, 0),
      Point(0, 0)
    ])

    # A stop at the far end of the loop
    stop = Point(1, 1)

    # A bus crossing the point at which the route loops
    bus_history = [
      Point(0.1,   0),
      Point(  0,   0),
      Point(  0, 0.1)
    ]

    # We're choosing a 'max_dist' radius such that it's
    # big enough to include stops reasonably close to the bus,
    # but not so big that it includes the stop at the far end.
    # Normally we'd just pick something like "ten meters", but
    # that doesn't work here, since we're using unrealistic
    # lat/long coords for simplicity.
    # ( (0,0) and (1,1) are hundreds of miles apart.)
    max_dist = haversine(Point(0, 0), Point(0.1, 0))

    # Going from the end of the route to the start
    # shouldn't count as passing the stop at the far end
    p = passes(bus_history, stop, route, max_dist = max_dist)
    self.assertFalse(p)

    # But we can pass a stop at the point at which the route loops
    p = passes(bus_history, Point(0,0), route, max_dist = max_dist)
    self.assertTrue(p)

  def test_passes_with_curvy_road_and_measurement_error(self):
    route = Polyline([
      Point(0, 0),
      Point(0, 0.1),
      Point(0.1, 0.2),
      Point(0.2, 0.2),
      Point(0.3, 0.3),
      Point(0.3, 0.4),
      Point(0.2, 0.5),
      Point(0.1, 0.5),
      Point(0, 0.6)
    ])

    stop = Point(0.1, 0.5)

    bus_history = [Point(0.25, 0.25), Point(0.29, 0.29)]
    p = passes(bus_history, stop, route)
    self.assertFalse(p)
    bus_history = [Point(0, 0), Point(0, 0.6)]
    p = passes(bus_history, stop, route)
    self.assertTrue(p)

  def test_passes_with_two_joined_paths(self):
    route1 = Polyline([
      Point(0,0),
      Point(0,10),
      Point(0,20)
    ])

    route2 = Polyline([
      Point(0,20),
      Point(0,30),
      Point(0,40)
    ])

    stop = Point(0, 19)

    bus_history = [Point(0, 17), Point(0, 22)]

    closest_route = route_histo({
      'route1': route1,
      'route2': route2
    }, bus_history)

    print(closest_route)

if __name__ == '__main__':
  unittest.main()
