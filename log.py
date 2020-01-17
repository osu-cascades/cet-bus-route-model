import json
import urllib.request
from bs4 import BeautifulSoup
import time
import sqlite3

conn = sqlite3.connect('test.db')
c = conn.cursor()

c.execute('''
  create table if not exists buslog (
    bus char(32) not null,
    lat char(32) not null,
    lon char(32) not null,
    heading char(8) not null,
    speed char(8) not null,
    received datetime,
    route char(16) not null default '',
    stopid char(16) not null default '',
    primary key(bus, received)
  );
''')

while True:
  req = urllib.request.urlopen('http://ridecenter.org:7016')
  html = req.read()
  soup = BeautifulSoup(html, 'html.parser').body.string
  bus_json = json.loads(soup)
  for bus in bus_json:
    vals = [
      bus['busNumber'],
      bus['latitude'],
      bus['longitude'],
      bus['heading'],
      bus['speed'],
      bus['received']
    ]
    print(vals)
    stmt = '''
      insert or ignore into buslog (bus,lat,lon,heading,speed,received) values (
        ?,
        ?,
        ?,
        ?,
        ?,
        ?
      );
    '''
    c.execute(stmt, vals)
  conn.commit()
  time.sleep(10)
