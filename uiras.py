#!/usr/bin/env python3

from io import StringIO
import json, csv
import urllib.request
import csv
from time import sleep

uirasurl = 'https://iot.fvh.fi/opendata/uiras/70B3D57050004DF8_v1.json'
davisurl = 'https://iot.fvh.fi/downloads/vasikka-weather.csv'

while True:
  try:
    with urllib.request.urlopen(uirasurl) as response:
      data = response.read()      # a `bytes` object
      text = data.decode('utf-8') # a `str`; this step can't be used if data is binary
      jsondata = json.loads(text)
      #print(json.dumps(jsondata, indent=4, sort_keys=True))
      if len(jsondata) > 0 and jsondata['data'][1].get('temp_water') is not None:
        temp_water = jsondata['data'][-1]['temp_water']
        #  else:
        # 'Value1' key does not exist
        #    pass
        print("Water: "+str(round(temp_water,1))+"C")
        with open("sensor.txt", "w") as f:
          f.write("Water: "+str(round(temp_water,1))+"C")

    with urllib.request.urlopen(davisurl) as response:
      data = response.read()      # a `bytes` object
      text = data.decode('utf-8') # a `str`; this step can't be used if data is binary
      reader = csv.reader(StringIO(text), delimiter=',')
      csvdata = []
      row = []
      for row in reader:
        if row or len(row) < 11:  # avoid blank & bad lines
          pass #Just read to last line
      with open("sensor.txt", "a") as f:
        print("Row: "+str(row)+"\n")
        if(row[2] != "255" and row[2] != "10minwind"):
          print("Wind: "+row[2]+"ms")
          f.write("\nWind: "+row[2]+"ms\n")
          print("Winddir: "+row[11]+"°")
          f.write("Winddir: "+row[11]+"°")
    sleep(2*60)
  except Exception as e:
    print(e)
