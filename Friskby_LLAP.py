


#!/usr/bin/env python3
""" 
This code reads LLAP data from Ciseco XRF radio and submits to FriskBy API
Its based on code from Ciseco - thank you!
Download LLAPSerial.py from https://github.com/CisecoPlc/LLAPtoCOSM
"""

import sys, time, Queue
import LLAPSerial
import urllib3
import requests
import json
import datetime
from time import gmtime, strftime

def ts():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

#Sensor mapping
# You have to define sensor mapping here, so it will fit the API sensors you define at FriskBy
sensors = {"DST": "XXXStoevXXXGate", "HUM": "XXXFuktXXXGate", "TMP": "XXXTempXXXGate", "AMB": "XXXLysXXXGate"} 
#API details
url = "http://friskby.herokuapp.com/sensor/api/reading/"
headers = {"Content-Type" : "application/json"}
api_key = "" # YOUR API KEY HERE

        
class LLAPFB:
    def __init__(self):
        self._running = True
        self.devid = "PI"
        self.port = "/dev/ttyAMA0"
        
  
        
        #setup serial bits
        self.queue = Queue.Queue()
        self.serial = LLAPSerial.LLAPSerial(self.queue)
    
    def __del__(self):
       pass
    
    def on_init(self):
        # connect serial on start
        self.serial.connect(self.port)
        print("Serial Connected")
        self._running = True
        print("Running")
    
    def main(self):
        if self.on_init() == False:
            self._running = False
    
        
        # loop
        while ( self._running ):
            try:
                self.on_loop()
            except KeyboardInterrupt:
                print("Keybord Quit")
                self._running = False
        self.disconnect_all()
            
    def disconnect_all(self):
        # disconnet serial
        self.serial.disconnect()
        


    def on_loop(self):
        if not self.queue.empty():
            llapMsg = self.queue.get()
            
            devID = llapMsg[1:3]
            payload = llapMsg[3:]
            print(llapMsg+" devID "+devID+" payload ", payload)
            
            #main state machine to handle llapMsg's
            if  payload.startswith('AAA'): # Initial data
                # remove trailing -
                data = payload[3:].replace("-","")                
                try:                    
                    global dl2 # Holds sensor data 
                    global numData # Number of sensors (sent from Arduino)
                    dl2 = {}
                    numData = int(data) #sensors                    
                except:
                    print ("ERR: " + payload[:3])
       	    elif payload.startswith('ZZZ'): # Last data
                i = 3
		data = payload[3:].replace("-","")		
		try:
                    
                    if len(dl2) == numData: # if we have the same amount of data as expected
                        
                        data = []
                        for key, value in dl2.iteritems(): # Add the data sent
                            data.append({"sensorid" : value[0] ,"timestamp" : value[1] , "value" : value[2], "key" : api_key})
                        
                        for measurement in data:
                                #data are posted to the API
                                try:
                                        response = requests.post( url , data = json.dumps( measurement ) , headers = headers )
                                        if response.status_code == 201:
                                                print("OK - {}".format(response.text))
                                        else:
                                                print("ERROR - posting failed")
                                                print("Status: {}".format(response.status_code))
                                                print("Msg: {}".format(response.text))
                                except:
                                        pass
                                          
                        dl2 = {} # empty datalist
                    else:
                        print "missing data"
                        print len(dl2) == numData
                        print dl2                 
		except:
		    print ("ERR: " + payload[:3])
		    
            else: # This handles all sensors               
                data = payload[3:].replace("-","")                
                try:
					# Add data
                    dl2[payload[:3]] = sensors[payload[:3]], datetime.datetime.utcnow().isoformat(), data
                except:
                    print ("ERR: " + payload[:3])

 
if __name__ == "__main__":
    application = LLAPFB()
    application.main()
