#!/usr/bin/python3 -u

import time
import argparse
import smbus
import os
import re
import threading
import signal
import traceback
from dataclasses import dataclass
from collections import deque

def bitExtract(number, anzahl, position): 
    return (((1 << anzahl) - 1) & (number >> (position))); 

def setBitAt(wert, position):
	return wert | (1<<position)
	
def tauscheBytes(wert):
	return int.from_bytes(wert.to_bytes(2,'big'),byteorder='little')
	
def read_word_data_swapped(bus,address,register):
	return tauscheBytes(bus.read_word_data(address,register))

def write_word_data_swapped(bus,address,register,data):
	bus.write_word_data(address,register,tauscheBytes(data))
	
	
def signal_handler(sig, frame):
	os._exit(0)
	
def init_Sensor(bus,address):
	config=read_word_data_swapped(bus,address,0x01)
	config=setBitAt(config,10) #auf kontinuierlich setzen
	write_word_data_swapped(bus,address,0x01,config)
	
		
def round_lux(lux):
	if args.round is not None:
		if args.round == 0:
			lux=int(round(lux,args.round))
		else:
			lux=round(lux,args.round)
	else:
		lux=round(lux,2) #to prevent floating point issues like Lux: 42.800000000000004 sensor output is generally only 2 decimal places
	return lux

def get_lux(bus,address):
	wert=read_word_data_swapped(bus,address,0x00)
	exponent= bitExtract(wert,4,12) 
	mantisse= bitExtract(wert,12,0)
	lsb_size = 0.01 * pow(2,exponent)
	lux=lsb_size * mantisse
	return lux
	

@dataclass
class Measurement:
	lux: float
	lux2: float = None
	timestamp: int = 0

measurements=deque()		
	
def thread_SendingData():
	global measurements
	path = os.path.dirname(os.path.abspath(__file__))
	while True:
		try:
			mea = measurements.popleft()
			fmt = "sensorname,lux" #don't try to seperate by semicolon ';' os.system will use that as command seperator
			params = args.name + " " + str(mea.lux)
			if mea.lux2 is not None:
				fmt +=",lux2"
				params += " " + str(mea.lux2)
			params += " " + str(mea.timestamp)
			fmt +=",timestamp"
			cmd = path + "/" + args.callback + " " + fmt + " " + params
			print(cmd)
			ret = os.system(cmd)
			if (ret != 0):
					measurements.appendleft(mea) #put the measurement back
					print ("Data couln't be send to Callback, retrying...")
					time.sleep(5) #wait before trying again
		except IndexError:
			#print("Keine Daten")
			time.sleep(1)
		except Exception as e:
			print(e)
			print(traceback.format_exc())	
	

parser=argparse.ArgumentParser()
parser.add_argument("--device","-d", help="Set the device adress in format 0xff",metavar='0xff')
parser.add_argument("--device2","-d2", help="Set the second device adress in format 0xff",metavar='0xff')
parser.add_argument("--round","-r", help="Round Lux value to N decimal place", type=int)
parser.add_argument("--every","-e", help="Measure every N seconds", type=int, metavar="N", default=1)

callbackgroup = parser.add_argument_group("Callback related functions")
callbackgroup.add_argument("--callback","-call", help="Pass the path to a program/script that will be called on each new measurement")
callbackgroup.add_argument("--name","-n", help="Give this sensor a name reported to the callback script", default="opt3001")
callbackgroup.add_argument("--name2","-n2", help="Give the second sensor a name reported to the callback script", default="opt3001_2")

args=parser.parse_args()
address = 0x44
address2 = None
if args.device:
	if re.match("0x[0-9a-fA-F]{2}",args.device):
		address=int(args.device,16)
	else:
		print("Please specify device address in format 0xYY like 0x44")
		os._exit(1)
else:
	parser.print_help()
	os._exit(1)
	
if args.device2:
	if re.match("0x[0-9a-fA-F]{2}",args.device2):
		address2=int(args.device2,16)
	else:
		print("Please specify second device address in format 0xYY like 0x45")
		os._exit(1)	
	
if args.callback:
	dataThread = threading.Thread(target=thread_SendingData)
	dataThread.start()

signal.signal(signal.SIGINT, signal_handler)	

bus = smbus.SMBus(1)

init_Sensor(bus,address)
if address2 is not None:
	init_Sensor(bus,address2)

#manufacturerID=read_word_data_swapped(bus,address,0x7E) #18772 0x4954
#deviceID=read_word_data_swapped(bus,address,0x7F) #304 0x0130
# print("Manufacturer ID: "+ hex(manufacturerID) + " als String " + manufacturerID.to_bytes(2,"big").decode())
# print("DeviceID: "+ hex(deviceID))
lux2=None
while True:

	lux=get_lux(bus,address)
	lux=round_lux(lux)
	res="Lux: " + str(lux)
	if address2 is not None:
		lux2=get_lux(bus,address2)
		lux2=round_lux(lux2)
		res+=", Lux2: " + str(lux2)
		
	
	print(res)
	if args.callback:
		measurement = Measurement(0,None,0)
		measurement.timestamp = int(time.time())
		measurement.lux=lux
		if lux2 is not None:
			measurement.lux2=lux2
		measurements.append(measurement)
	time.sleep(args.every)
