from .geo import Point
from .haversine import haversine
import math
import unittest

class TestHaversine(unittest.TestCase):
  def assertClose(self, expected, actual, tolerance):
    err = abs(expected - actual)
    rel_err = err / max(abs(actual), abs(expected))
    self.assertLess(rel_err, tolerance)

  def test_haversine(self):
    d = haversine(
      Point(50.06638889, 5.71472222),
      Point(58.64388889, 3.07000000)
    )
    self.assertClose(968900, d, tolerance=0.01)

    d = haversine(
      Point(0, 0),
      Point(0, 0)
    )
    self.assertEqual(0, d)
