#!/usr/bin/env python3
#
# actor.py -- actor for AppStudio geolocation demo. Simulates a moving object with a random lifespan.
#
# Author: Fernando Sanchez [ fernando at mesosphere.com ]
#
# * receives as environment variables:
# - DEFAULT_TRAJECTORY 			# whether it's RANDOM or FILE
# - ROUTES_FILENAME 			# in case the file is not routes.csv
# - AGE/TEMP/SPEED MAX/MIN		# ranges
# - LATITUDE 					# starting position
# - LONGITUDE 					# starting position
# - RADIUS 					# max radius of movement in meters
# - LISTENER 					# API endpoint to post updates to 
# - APPDEF 					# List-of-JSONs definition of the AppStudio environment
# - WAIT_SECS_SEED				# order of magnitude in seconds of period after which we consider change or die
# - MOVING_CHANCE 				# % probability of position change each WAIT_SECS_SEED seconds
# - SUICIDE_CHANCE				# % probability of exiting each WAIT_SECS_SEED seconds

import sys
import os
import requests
import json
import random
from faker import Faker		#fake-factory: generates good-looking random data
import datetime
import time 				
import math

#default values
################

DEFAULT_TRAJECTORY = "RANDOM"		#RANDOM, or URI with routes/locations file $LOCATION_FILENAME
DEFAULT_ROUTES_FILENAME = "routes.csv"
DEFAULT_LATITUDE = 41.411338		#SF bay
DEFAULT_LONGITUDE = 2.226438
#DEFAULT_LATITUDE = 40.773860		#NYC central park
#DEFAULT_LONGITUDE = -73.970813
DEFAULT_RADIUS = 300
DEFAULT_MY_ID_LENGTH = 6			#up to 1 million users - integer
DEFAULT_AGE_MAX = 60
DEFAULT_AGE_MIN = 16
DEFAULT_TEMP_MAX = 100
DEFAULT_TEMP_MIN = 50
DEFAULT_SPEED_MIN = 10
DEFAULT_SPEED_MAX = 120
DEFAULT_WAIT_SECS_SEED = 5			#wait cycle seed for random (seconds)
DEFAULT_MOVING_CHANCE = 66			#chance of moving in the map every wait cycle
DEFAULT_SUICIDE_CHANCE = 2			#chance of commiting suicide in pct every wait time

RESERVED_FIELDS = ("location", "id", "event_timestamp") #fields that should remain unchanged
STATUS_TYPES = ['HEALTHY','NEEDS SERVICE','DATA ERRORS','HEALTHY','HEALTHY','HEALTHY']
DEFAULT_BUFSIZE = 1024 * 1024		#1 MB - size of buffer for lines read from the "routes"

#helper functions
#################

def random_number( min=0, max=0, length=0 ):
	"""
	Generates a random number inside a range or with a specific length and returns as a string
	"""
	if length > 0:
		range_start = 10**( length - 1 )
		range_end = ( 10**length ) - 1
		return str(random.randint( range_start, range_end ))
	if (min and max):
		return str(random.randint( min, max ))

def random_for_type( field ):
	"""
	Generates a random value for the field received.
	field: {
		"name": name, 
		"type": JStype, 
		"pivot": boolean
		}
	Type is a JS type defined by the app, not a python type.
	"""

	my_type = field['type']
	my_name = field['name']

	if my_type == "String": return fake.bs() 
	if my_type == "Boolean": return bool(random.getrandbits(1)) 	
	if my_type == "Integer": return random_number( length=2 )		
	if my_type == "Long": return random_number( length=5 )
	if my_type == "Double": return random_number( min=(-1)*random_number( length=7 ) , \
							max=random_number( length=7 ) )			
	if my_type == "Location": return str(fake.latitude())+","+str(fake.longitude()) 
	if ( my_type == "Date/time" or my_type == "Date/Time" ): 
		date = fake.iso8601()[:-3]+'Z' #fake date -- ANY date || Converted to Zulu for Kibana
		#date = datetime.datetime.now().isoformat()
		return(date)

	print('**ERROR: random_for_type: my_type is not detected')
	return None

def realistic_for_type( field ):
	"""
	Generates a realistic value for the field received.
	field: {
		"name": name, 
		"type": JStype, 
		"pivot": boolean
		}
	Type is a JS type defined by the app, not a python type.
	"""

	my_type = field['type']
	my_name = field['name']

	#generate realistic values for well-known fields
	#generic
	if my_name == "uuid": return random_number( length=DEFAULT_MY_ID_LENGTH )
	#taxi
	if my_name == "observationTime": return int(time.time())									# "now" standard	
	if my_name == "geometry": return random_location( Latitude, Longitude, Radius ) 	#taxi app with Esri term
	if my_name == "passengerCount": return random_number( min=1, max=6 )		#or str(random.randint( 1, 6 ))
	#taxi, event
	if my_name == "route_length": return 1
	if my_name == "name": return fake.name()
	if my_name == "age": return random_number( min=Age_min, max=Age_max )
	if my_name == "country": return fake.country()
	#connected car
	if my_name == "driver": return fake.name()
	if my_name == "motortemp": return random_number( min=Temp_min, max=Temp_max )	#or str(random.randint( 50, 100 ))
	if my_name == "speed": return random_number( min=Speed_min, max=Speed_max )		
	if my_name == "carid": return random_number( length=DEFAULT_MY_ID_LENGTH )		
	if my_name == "status": return random.choice( STATUS_TYPES ) 	#STATUS_TYPES[random.randint(0,len(STATUS_TYPES)-1)]		

	return None

def random_location( latitude, longitude, radius ):
	"""
	Generates a random location from lat, long, radius
	returns in as string in "latitude", "longitude" format.
	Adapted to trim numbers to exactly [2d].[6d],[2d].[6d].
	Without trimming, I get 
	"40.77672360606691,-73.96714029899"
	"""

	rd = float(radius) / 111300

	y0 = float(latitude)
	x0 = float(longitude)

	u = random.uniform(0,1)
	v = random.uniform(0,1)

	w = rd*math.sqrt(u)
	t = 2*math.pi*v
	x = w*math.cos(t)
	y = w*math.sin(t)

	#exactly 6 decimals
	new_location = "{0:.6f}".format(round((y+y0),6))+","+"{0:.6f}".format(round((x+x0),6))

	return new_location

def bufcount(filename):
	"""
	Open up a file and read a certain chunk determined by a buffer, return the lines in the chunk.
	"""

	buf_size = DEFAULT_BUFSIZE 
	
	try:
		f = open( filename )	#the routes/trajectory file is a URI so should be downloaded to /
	except IOError:
		print("**ERROR: Trajectory set but file {0} not found.".format(filename))
		exit(1)

	lines = 0
	read_f = f.read # loop optimization
	buf = read_f(buf_size)

	while buf:
		lines += buf.count('\n')
		buf = read_f(buf_size)
	f.close()

	return lines

def yieldlines(thefile, whatlines):
	"""
	Return a specific number of lines from a file
	"""
	
	return (x for i, x in enumerate(thefile) if i in whatlines)

def format_location( lat_long ):
	"""
	Formats a received location to six decimals.
	"""

	loc_list = lat_long.split(",") 
	lat = float(loc_list[1])
	lon = float(loc_list[0])
	new_location = "{0:.6f}".format(round((lat),6))+","+"{0:.6f}".format(round((lon),6))

	return new_location

def calculate_distance (src_coords, dst_coords):
	"""
	Calculates the distance in meters between two coordinates.
	These are received as a string with "lat,long".
	"""

	R = 6373.0	#earth radius in km

	lat1, lon1 = src_coords.split(',')
	lat2, lon2 = dst_coords.split(',')

	lat1 = float(lat1)
	lon1 = float(lon1)
	lat2 = float(lat2)
	lon2 = float(lon2)

	# convert decimal degrees to radians 
	lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

	# haversine formula 
	dlon = lon2 - lon1 
	dlat = lat2 - lat1 
	a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
	c = 2 * math.asin(math.sqrt(a)) 
	distance_meters = R * c * 1000 # *1000 is km to m   

	return distance_meters

# Main Loop
###########

if __name__ == "__main__":

	fake = Faker()		#fake data factory

	# Parse environment variables
	Trajectory = os.getenv('TRAJECTORY', DEFAULT_TRAJECTORY)
	Routes_filename = os.getenv('ROUTES_FILENAME', DEFAULT_ROUTES_FILENAME)
	File_location = os.getenv("MESOS_SANDBOX","/mnt/mesos/sandbox")+"/"+Routes_filename
	Latitude = os.getenv('LATITUDE', DEFAULT_LATITUDE)
	Longitude = os.getenv('LONGITUDE', DEFAULT_LONGITUDE)
	Radius = os.getenv('RADIUS', DEFAULT_RADIUS)
	Age_min = os.getenv('AGE_MIN', DEFAULT_AGE_MIN)
	Age_max = os.getenv('AGE_MAX', DEFAULT_AGE_MAX)
	Temp_min = os.getenv('TEMP_MIN', DEFAULT_TEMP_MIN)
	Temp_max = os.getenv('TEMP_MAX', DEFAULT_TEMP_MAX)
	Speed_min = os.getenv('SPEED_MIN', DEFAULT_SPEED_MIN)
	Speed_max = os.getenv('SPEED_MAX', DEFAULT_SPEED_MAX)
	Wait_secs_seed = float(os.getenv('WAIT_SECS_SEED', DEFAULT_WAIT_SECS_SEED))
	Moving_chance = int(os.getenv('MOVING_CHANCE', DEFAULT_MOVING_CHANCE))
	Suicide_chance = int(os.getenv('SUICIDE_CHANCE', DEFAULT_SUICIDE_CHANCE))

	#Initialize actor
	actor = {}
	#RESERVED fields 
	actor['location'] = random_location( Latitude, Longitude, Radius )
	actor['id'] = int(time.time() * 1000)
	#event_timestamp for "now" in ISO8601-Z format
	temp_date = datetime.datetime.utcnow().isoformat() 	#now in ISO8601 
	timestamp_8601_Z = temp_date[:-3]+'Z'				#Reformat UTC-Zuly "2017-04-26T07:05:00.91Z"
	actor['event_timestamp'] = timestamp_8601_Z

	#Initialize location if Trajectory is not RANDOM and is passed as file.
	if Trajectory != "RANDOM":
		print("**INFO: Trajectory is set from {0}".format(File_location))
		numlines = bufcount(File_location)			#count number of lines that fit in buffer from the route file
		numlines = numlines - 1
		start_pos = random.randint( 0, numlines )	#randomly choose the position in the file
		end_pos = start_pos + 1000					#my route has 1000 points. TODO: randomize
		if end_pos > numlines:
			end_pos = numlines						#cap end_pos at end of file
	
		route_range = set(range(start_pos,end_pos))
		f=open(File_location)
		route=list(yieldlines(f,route_range))
		route_index=0
	else:
		print("**INFO: Trajectory is random")

	# AppStudio: connect with listener
	listener = os.getenv('LISTENER')
	print('**INFO: Will connect to Listener at: {0}'.format( listener ) )

	# AppStudio: read AppDef "fields"
	appdef_env = os.getenv('APPDEF', {} )
	if appdef_env:
		appdef_clean = appdef_env.replace( "'", '"' )	#need double quotes
		print('**INFO: Application Definition is: {0}'.format( appdef_clean ) )
		appdef = json.loads(appdef_clean)
		fields = appdef['fields']
	else:	
		appdef_clean = ""
		fields = []

	#loop through the fields, populate
	for field in fields:

		#skip well-known fields
		if field['name'] in RESERVED_FIELDS: 
			print('**DEBUG: RESERVED field: {0} | value: {1}'.format( field['name'], actor[field['name']] ) )
			continue

		#Customize values that makes sense for well-known fields
		actor[field['name']] = realistic_for_type( field )
		if actor[field['name']]:					#it's a known field so it was populated as realistic
			print('**DEBUG: KNOWN field: {0} | realistic: {1}'.format( field['name'], actor[field['name']] ) )
			continue

		#Any field that is not well-known and LEARNED from APPDEF, fill it with random stuff
		actor[field['name']] = random_for_type( field )
		print('**DEBUG: LEARNED field: {0} | randomized: {1}'.format( field['name'], actor[field['name']] ) )

	# Main loop
	while True:

		#RESERVED fields:
		actor['id'] = int(time.time() * 1000)				#my ID is "now"

		#event_timestamp: "now" in ISO8601-Z format
		temp_date = datetime.datetime.utcnow().isoformat() 	#now in ISO8601 
		timestamp_8601_Z = temp_date[:-3]+'Z'				#Reformat UTC-Zuly "2017-04-26T07:05:00.91Z"
		actor['event_timestamp'] = timestamp_8601_Z
		print('**DEBUG: event_timestamp is: {0}'.format( timestamp_8601_Z ) )

		#build request
		headers = {
		'Content-type': 'application/json'
		}
		#send request
		try:
			request = requests.post(
				listener,
				data = json.dumps( actor ),
				headers = headers
				)
			request.raise_for_status()
			print("**INFO: sent update: \n{0}".format(actor))
		except (
		    requests.exceptions.ConnectionError ,\
		    requests.exceptions.Timeout ,\
		    requests.exceptions.TooManyRedirects ,\
		    requests.exceptions.RequestException ,\
		    ConnectionRefusedError
		    ) as error:
			print ('**ERROR: update failed {}: {}'.format( actor, error ) ) 

		#randomly decide if dying 
		commit_suicide = ( random.randrange(100) < Suicide_chance )
		if commit_suicide:
			print("**INFO: This party sucks. I'm out of here.")
			sys.exit(0)

		#wait a random amount of time
		wait_interval = Wait_secs_seed*int(random_number( length=1 ))
		print("**INFO: I'm going to wait here for {0} seconds.".format(wait_interval))
		time.sleep(wait_interval)

		#randomly decide if moving
		move_on = ( random.randrange(100) < Moving_chance )
		if move_on:
			
			#randomly decide where to move to, in a radius or from a set of locations in a trajectory.
			print("**INFO: Let's move somewhere else.")
			current_lat, current_lon = actor["location"].split(",")
			print("**INFO:  My current location is {0},{1}".format( current_lat, current_lon ))
			if Trajectory == "RANDOM":
				new_location = random_location( current_lat, current_lon, Radius )
			else:	#trajectory comes from a file and has been put on the "route" list
				new_location = format_location(route[route_index].rstrip())
				route_index +=1					#continue along the route of set points
			print("**INFO:  My new location will be {0}".format( new_location ) )		
			distance = calculate_distance( actor['location'], new_location )
			print("**INFO: I'm going to move {0} meters".format( distance ) )
			
			#keep track of how much I move.
			if 'route_length' in actor:
				actor['route_length'] += int(distance)
			actor['location'] = new_location
