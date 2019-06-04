#!/usr/bin/python3
import csv
import datetime as dt
import json
import os
import pytz
import re
import sys
import syslog
from twilio.rest import Client
from dateutil.relativedelta import relativedelta

try:
  js = open(os.path.join(sys.path[0], '/configs/config.json')).read()
  config = json.loads(js)
except:
  syslog.syslog(syslog.LOG_ALERT, "Unable to load nwswarn config file.")
  exit(1)

warning_types = {'SVR':'severe thunderstorm warning',
                 'TOR':'tornado warning',
                 'FFW':'flash flood warning'}

class nwszones(dict):
  def __init__(self,zonefile):
    class _zone:
      def __init__(self,state,code,county):
        self.state = state
        self.code = code
        self.county = county
    states = {}
    zones = []
    with open(os.path.join(sys.path[0], 'sorted_fips.txt'), newline = '') as zone_file:
      Z = csv.reader(zone_file,delimiter=' ')
      for z in Z:
        zones.append(z)
        if z[0] not in states.keys():
          states[z[0]] = []
        states[z[0]].append(_zone(z[0],z[1],z[2]))
    for k in states.keys():
      self[k] = states[k]

class wmoheader:
  def __init__(self,infile):
    lineList = [line.rstrip('\n') for line in open(infile)]
    for n,l in enumerate(lineList):
      if len(l) == 6:
        self.wtype = l[0:3]
        self.wfo = l[3:6]
        self.header = lineList[0:n+3]

class warning:
  def __init__(self,header,Zones):
    self.wtype = header.header[-3][0:3]
    self.wfo = header.header[-3][3:6]
    county_time  = header.header[-2].split('-')  # split by dashes
    county_time  = list(filter(None, county_time))  # remove empty elements
    self.endtime = str(county_time[-1])
    self.endtime = (int(self.endtime[0:2]),int(self.endtime[2:4]),int(self.endtime[4:6]))
    _counties  = str('-').join(county_time[0:-1])
    pattern = "[A-Z][A-Z]C"
    states = re.findall(pattern,_counties)
    states = [x[0:-1] for x in states]
    _counties = re.split(pattern,_counties)[1::]
    _counties = [x.split('-') for x in _counties]
    _counties = [list(filter(None,x)) for x in _counties]
    self.counties = dict(zip(states,_counties))
    self.countynames = []
    for s in self.counties.keys():
      for c in self.counties[s]:
        for C in Zones[s]:
          if int(c) == int(C.code):
            self.countynames.append(C.county)

def sendsms(twilio_config,to,body):
  client = Client(twilio_config['account_sid'], twilio_config['auth_token'])
  message = client.messages.create(body=sms,from_='+'+str(twilio_config['origin']),to='+'+str(to))
  return message.sid

def format_endtime(endtime,fmt='%Y-%m-%d %H:%M:%S %Z%z'):
  est = pytz.timezone('US/Eastern')
  utc = pytz.utc
  curtime = dt.datetime.utcnow().timetuple()[0:5]
  endtime = tuple(list(curtime[0:2])+list(endtime))
  Curtime = dt.datetime(*curtime,tzinfo=utc)
  Endtime = dt.datetime(*endtime,tzinfo=utc)
  if Endtime < Curtime:
    Endtime = Endtime + relativedelta(months=1)
  return Endtime.astimezone(est).strftime(fmt)

if __name__ == "__main__":
  infile = sys.argv[1]
  header = wmoheader(infile)
  if header.wtype not in ['TOR','SVR','FFW']:
    exit(1)
  if header.wfo not in ['PHI','OKX']:
    exit(1)
  Zones = nwszones('counties.txt')
  W = warning(header,Zones)
  if len(W.countynames) > 0:
    valid_until = format_endtime(W.endtime,fmt='%-I:%M %p')
    sms = 'NWS issued '+W.wtype+' for '+', '.join(W.countynames)+' counties until '+valid_until
  else:
    raise ValueError('County list is empty.')
  _ = sendsms(config['twilio'],config['notify']['destination'],sms)
  exit(0)
