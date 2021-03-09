#!/usr/bin/env python3
import math
from matplotlib import path
from datetime import datetime, date,  timedelta
from time import sleep
#from youtubechat import YoutubeLiveChat, get_live_chat_id_for_stream_now
import urllib.parse
import requests
import settings
import inspect, os.path

#Get current path that our .py is in
myfilename = inspect.getframeinfo(inspect.currentframe()).filename
mypath     = os.path.dirname(os.path.abspath(myfilename))

debug_only = False  # if True only check that queries work, but do not send to youtube

#if not debug_only:
#    livechat_id = get_live_chat_id_for_stream_now("oauth_creds")
#    chat_obj = YoutubeLiveChat("oauth_creds", [livechat_id])

# Vasikkasaari  60.153438, 25.011680
# Kustaanmiekan suunta / vasen raja  60.143621, 24.993100
# Lonnan edusta 60.158087, 24.984143
# Katajanokasta itään 60.167353, 24.986588
boundingPoints = path.Path([(25.011680, 60.153438), (24.993100, 60.143621),
                            (24.984143, 60.158087), (24.986588, 60.167353)])

shipReports = {}

def respond(msgs, chatid):
    for msg in msgs:
        print(msg)
        if( str(msg)[:6]=="aisbot" ):
            chat_obj.send_message("Hello", chatid)
        msg.delete()

# Utility function for calculate radius for vessel query, https://gist.github.com/rochacbruno/2883505
def distance(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c
    return d

def aisbot():
    print("Starting AIS bot")
    #if not debug_only:
    #    chat_obj.send_message("Starting AIS bot", livechat_id)
    #send_youtube_chat_message(live_chat_id, "Starting AIS bot")

    # define central point and radius for location query
    x = [p[0][0] for p in boundingPoints.iter_segments()]
    y = [p[0][1] for p in boundingPoints.iter_segments()]

    centroid = (sum(x) / len(boundingPoints),
                sum(y) / len(boundingPoints))
    max_distance = 0
    for p in boundingPoints.iter_segments():
        max_distance = max(max_distance, distance(p[0], centroid))

    while True:
        # query for vessels aound the cnetroid
        utc_datetime = datetime.utcnow() - timedelta(hours=2)
        firstdate = utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        request_url = settings.location_query_base.format(
            centroid[1], centroid[0], max_distance, urllib.parse.quote(firstdate))

        try:
            response = None
            response = requests.get(request_url)
            locations = response.json()
        except Exception as ex:
            print(ex)
            print('Errors in the location response:')
            if response is not None:
                print(response)
            locations = dict()
            locations['features'] = dict()

        if debug_only:
            print(locations)

        trackedShips=0
        for feature in locations['features']:
            mmsi = feature['mmsi']
            coordinates = feature['geometry']['coordinates']
            speed = feature['properties']['sog']

            since_last_report_secs = settings.min_ship_report_interval_secs
            if mmsi in shipReports:
                if shipReports[mmsi]:
                    since_last_report_secs = (
                        datetime.utcnow()-shipReports[mmsi]).total_seconds()

            in_view = boundingPoints.contains_points(
                [coordinates])  # is vessel inside polygon

#and (since_last_report_secs >= settings.min_ship_report_interval_secs) 
            if ((in_view and (speed > settings.min_speed_to_report)) or debug_only):
                trackedShips=trackedShips+1
                heading = feature['properties']['heading']
                vessel_request_url = settings.vessel_query_base.format(
                    str(mmsi))

                shipdata_ok = False
                try:
                    shipdataresp = None
                    shipdataresp = requests.get(vessel_request_url)
                    shipdata = shipdataresp.json()
                    shipdata_ok = True
                except Exception as ex:
                    print(ex)
                    print('Errors in the shipdata response:')
                    if shipdataresp is not None:
                        print(shipdataresp)
                if shipdata_ok:
                    shipnName = shipdata['name']
                    destination = shipdata['destination']
                    direction = 0  # RFU
                    shipType = shipdata['shipType']
                    if shipType in settings.shipTypes:
                        shipTypeStr = settings.shipTypes[shipType]
                    else:
                        shipTypeStr = 'unknown ({:d})'.format(shipType)

                    heading = heading % 360  # to fix errornous headings > 360
                    heading_round = int(45*((heading+23)//45))
                    if heading_round in settings.directions:
                        heading_round_str = settings.directions[heading_round]
                    else:
                        heading_round_str = str(heading)
                        print('Invalid rounded heading {:d} from {:d} '.format(
                            heading_round, heading))

                    msgText = '{:s} ({:s}) to {:s}, speed {:3.1f} kn {:s}/{:d} '.format(shipnName, shipTypeStr,
                                                                                        destination, speed, heading_round_str, heading)
                    # ° - mene läpi serialisoinnista linuxilla vaikka menee macilla
                    # raise TypeError(repr(o) + " is not JSON se rializable")
                    # TypeError: b'VIKING XPRS (Passenger) to HELSINKI=TALLINN, speed 14.8 kn North/14\xc2\xb0 ' is not JSON serializable

                    print(str(datetime.utcnow()) + msgText)
                    mode='w' #Create new file for first ship
                    if( trackedShips > 1 ):
                        mode='a' #Append for other ships
                    with open(mypath+'/ais.txt', mode) as f:
                        if( trackedShips > 1 ):
                            f.write('\n')
                        f.write(msgText)
                        #send_youtube_chat_message(live_chat_id,msgText)
                        #chat_obj.send_message(msgText, livechat_id)

                    shipReports[mmsi] = datetime.utcnow()
                    
        if ( trackedShips==0 ):
            #print("Clear ais.txt")
            with open(mypath+'/ais.txt', 'w') as f:
                f.write("")

#        if ((datetime.utcnow().minute % 10) == 0):
#            print(datetime.utcnow())
#        else:
#            print('.')

        sleep(settings.update_period_secs)

#MAIN program
aisbot()
