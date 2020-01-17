import unittest

from bus_history import BusHistory

class TestBusHistory(unittest.TestCase):
  def test_init(self):
    hist = BusHistory(10)
    self.assertEqual(hist.get(), [])

  def test_push(self):
    hist = BusHistory(10)
    hist.push(99)
    self.assertEqual(hist.get()[0], 99)

  def test_capacity(self):
    hist = BusHistory(10)
    for i in range(0, 10):
      hist.push(i)
    self.assertEqual(hist.get()[0], 0)
    self.assertEqual(hist.get()[9], 9)

    hist.push(10)
    self.assertEqual(hist.get()[0], 1)
    self.assertEqual(hist.get()[9], 10)
