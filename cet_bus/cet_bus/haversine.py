import math

# 2pi over 360
DEG_TO_RAD = 0.0174533

def to_radians(degrees):
  return DEG_TO_RAD * degrees

# The haversine function gets the distance in meters between two
# lat/lon coordinate pairs.
def haversine(p1, p2):
  R = 6371e3
  lat1 = to_radians(p1.x)
  lat2 = to_radians(p2.x)
  del_lat = to_radians(p2.x - p1.x)
  del_lon = to_radians(p2.y - p1.y)
  a =\
    math.sin(del_lat / 2) ** 2 +\
    math.cos(lat1) * math.cos(lat2) *\
    math.sin(del_lon / 2) ** 2
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
  return R * c
