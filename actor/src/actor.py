#!/usr/bin/env python3
#
# actor.py -- actor for AppStudio geolocation demo. Simulates a moving object with a random lifespan.
#
# Author: Fernando Sanchez [ fernando at mesosphere.com ]
#
# * receives as environment variables:
# - LATITUDE 					# starting position
# - LONGITUDE 					# starting position
# - RADIUS 					# max radius of movement in meters
# - LISTENER 					# API endpoint to post updates to 
# - APPDEF 					# List-of-JSONs definition of the AppStudio environment
# - WAIT_SECS_SEED				# order of magnitude in seconds of period after which we consider change or die
# - MOVING_CHANCE 				# % probability of position change each WAIT_SECS_SEED seconds
# - SUICIDE_CHANCE				# % probability of exiting each WAIT_SECS_SEED seconds
# * Not currently used:
# - amount of change in meters (speed-like)	# use "RADIUS"
# - duration/lifespan				# use "SUICIDE_CHANCE"


#load environment variables
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

DEFAULT_LATITUDE = 40.773860   #NYC central park
DEFAULT_LONGITUDE = -73.970813
#DEFAULT_LATITUDE = 40.453062	#Madrid stadium
#DEFAULT_LONGITUDE = -3.688334
#DEFAULT_LATITUDE = 48.858554	#Eiffel tower
#DEFAULT_LONGITUDE = 2.294513
DEFAULT_RADIUS = 300
DEFAULT_MY_ID_LENGTH = 6			#up to 1 million users - integer
DEFAULT_AGE_MAX = 60
DEFAULT_AGE_MIN = 16
DEFAULT_WAIT_SECS_SEED = 20			#every random*(THIS seconds) we consider  moving
DEFAULT_MOVING_CHANCE = 33			#chance of moving in the map
DEFAULT_SUICIDE_CHANCE = 2			#chance of commiting suicide in pct every wait time

#helper functions
#################

def generate_random_number( min=0, max=0, length=0 ):
	"""
	Generates a random number inside a range or with a specific length
	"""
	if length > 0:
		range_start = 10**( length - 1 )
		range_end = ( 10**length ) - 1
		return random.randint( range_start, range_end )
	if (min and max):
		return random.randint( min, max )

def get_random_for_type( field ):
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

	print('**DEBUG: Random value for {0} of type {1}'.format(my_name, my_type))

	if my_type == "String": return fake.bs() 
	if my_type == "Boolean": return bool(random.getrandbits(1)) 	
	if my_type == "Integer": return generate_random_number( length=2 )		
	if my_type == "Long": return generate_random_number( length=5 )
	if my_type == "Double": return generate_random_number( min=(-1)*generate_random_number( length=7 ) , \
							max=generate_random_number( length=7 ) )			
	if my_type == "Location": return str(fake.latitude())+","+str(fake.longitude()) 
	if ( my_type == "Date/time" or my_type == "Date/Time" ): 
		date = fake.iso8601()[:-3]+'Z' #fake date -- ANY date || Converted to Zulu for Kibana
		#date = datetime.datetime.now().isoformat()
		print("**DEBUG: fake date is: {0}".format(date))
		return(date)

	print('**ERROR: my_type is not detected')
	return None

def generate_random_location( latitude, longitude, radius ):
	"""
	Generates a random location from lat, long, radius
	returns in as string in "latitude", "longitude" format.
	Adapted to trim numbers to exactly [2d].[6d],[2d].[6d].
	Without trimming, I get 
	"40.77672360606691,-73.96714029899"
	"""

	rd = float(radius) / 111300

	print("**DEBUG: generate random location with {0} m radius from {1},{2}".format(radius, latitude, longitude))

	y0 = float(latitude)
	x0 = float(longitude)

	u = random.uniform(0,1)
	v = random.uniform(0,1)

	print("**DEBUG: seeds are {0} and {1}".format( u, v ) )

	w = rd*math.sqrt(u)
	t = 2*math.pi*v
	x = w*math.cos(t)
	y = w*math.sin(t)

	#exactly 6 decimals
	new_location = "{0:.6f}".format(round((y+y0),6))+","+"{0:.6f}".format(round((x+x0),6))
	print('**DEBUG: new_location is {0}'.format(new_location))

	return new_location

def calculate_distance (src_coords, dst_coords):
	"""
	Calculates the distance in meters between two coordinates.
	These are received as a string with "lat,long".
	"""

	R = 6373.0	#earth radius in km

	print("**DEBUG: received src {0} and dst {1}".format(src_coords, dst_coords))
	lat1, lon1 = src_coords.split(',')
	lat2, lon2 = dst_coords.split(',')

	lat1 = float(lat1)
	lon1 = float(lon1)
	lat2 = float(lat2)
	lon2 = float(lon2)

	# convert decimal degrees to radians 
	lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

	print("**DEBUG: coords in radians are: src is {0},{1} | dst is {2} {3}".format(lat1, lon1, lat2, lon2))

	# haversine formula 
	dlon = lon2 - lon1 
	dlat = lat2 - lat1 
	a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
	c = 2 * math.asin(math.sqrt(a)) 
	distance_meters = R * c * 1000 # *1000 is km to m   

	print("**DEBUG: distance METERS is {0}".format(distance_meters))

	return distance_meters

# Main Loop
###########

if __name__ == "__main__":

	fake = Faker()		#fake data factory

	#TODO: Actors that re-live?
	# check in Cassandra whether I exist? relaunch if I do?
	actor = {}
	#set creation time
	#actor["start_time"] = datetime.datetime.now().isoformat()[:-3]+'Z' #adapted to Zulu for Kibana

	# Parse environment variables
	Latitude = os.getenv('LATITUDE', DEFAULT_LATITUDE)
	Longitude = os.getenv('LONGITUDE', DEFAULT_LONGITUDE)
	Radius = os.getenv('RADIUS', DEFAULT_RADIUS)
	My_id_length = os.getenv('MY_ID_LENGTH', DEFAULT_MY_ID_LENGTH)
	Age_min = os.getenv('AGE_MIN', DEFAULT_AGE_MIN)
	Age_max = os.getenv('AGE_MAX', DEFAULT_AGE_MAX)
	Wait_secs_seed = os.getenv('WAIT_SECS_SEED', DEFAULT_WAIT_SECS_SEED)
	Moving_chance = os.getenv('MOVING_CHANCE', DEFAULT_MOVING_CHANCE)
	Suicide_chance = os.getenv('SUICIDE_CHANCE', DEFAULT_SUICIDE_CHANCE)
	listener = os.getenv('LISTENER')
	print('**DEBUG: Listener is: {0}'.format( listener ) )

	#APPDEF: read "fields"
	appdef_env = os.getenv('APPDEF', {} )
	if appdef_env:
		appdef_clean = appdef_env.replace( "'", '"' )	#need double quotes
		print('**APPDEF clean is: {0}'.format( appdef_clean ) )
		appdef = json.loads(appdef_clean)
		fields = appdef['fields']
	else:
		appdef_clean = ""
		fields = []

	#loop through the fields, populate
	for field in fields:

		##### CUSTOMIZE VALUES FOR KNOWN FIELDS --- To look realistic / fit to boundaries / etc
		#######################################################################################

		#search for "uuid", if present ignore and create unique ID.
		if field['name'] == "uuid":
			actor["uuid"] = generate_random_number( length=My_id_length )
			print('**DEBUG: my uuid is: {0}'.format( actor["uuid"] ) )
			print('**DEBUG: APPDEF gives me {0} but my {1} will remain at {2} as generated'.format( field['name'],field['name'],actor[field['name']] ) )
			continue

		#TAXI: earch for "location", if present ignore it as location is passed as a parameter
		if field['name'] == "location":
			#Generate my location from lat long radius
			print("Initial location is {0},{1}".format( Latitude, Longitude ))
			actor["location"] = generate_random_location( Latitude, Longitude, Radius )
			print('**DEBUG: APPDEF gives me {0} but my {1} will remain at {2} as generated'.format( field['name'],field['name'],actor[field['name']] ) )
			continue

		#TAXI: search for "observationTime", if present generate a "now" time
		if field['name'] == "observationTime":
			actor["observationTime"] = int(time.time())
			print('**DEBUG: my {0} is: {1}'.format( field['name'], actor[field['name']] ) )
			continue

		#TAXI: search for "geometry", if present copy location (this is to adapt to the GUI naming)
		if field['name'] == "geometry":
			actor["geometry"] = actor["location"]
			print('**DEBUG: my {0} is: {1}'.format( field['name'], actor[field['name']] ) )
			continue

		#TAXI: search for "passengerCount", if present do integer to string (this is to adapt to the GUI naming)
		if field['name'] == "passengerCount":
			actor["passengerCount"] = str(random.randint( 1, 6 ))
			print('**DEBUG: my {0} is: {1}'.format( field['name'], actor[field['name']] ) )
			continue

		#EVENT: search for "route_length", if present initialize to 0 and use for distance covered
		if field['name'] == "route_length":
			actor["route_length"] = 0		
			print('**DEBUG: APPDEF gives me {0} but my {1} will remain at {2} as generated'.format( field['name'],field['name'],actor[field['name']] ) )
			continue		

		#EVENT: search for "name", if present generate one
		if field['name'] == "name":
			actor["name"] = fake.name()
			print('**DEBUG: my {0} is: {1}'.format( field['name'], actor[field['name']] ) )
			continue

		#EVENT: search for "age", if present generate age in range that makes sense
		if field['name'] == "age":
			actor["age"] = generate_random_number( min=Age_min, max=Age_max )
			print('**DEBUG: my {0} is: {1}'.format( field['name'], actor[field['name']] ) )
			continue

		#EVENT: search for "country", if present generate a country name
		if field['name'] == "country":
			actor["country"] = fake.country()
			print('**DEBUG: my {0} is: {1}'.format( field['name'], actor[field['name']] ) )
			continue

		#DEMO: Anything else is LEARNED from APPDEF, fill it with random stuff
		actor[field['name']] = get_random_for_type( field )
		print('**DEBUG: LEARNED field: {0} | randomized is: {1}'.format( field['name'], actor[field['name']] ) )

	# Main loop
	while True:

		#my ID is "now"
		actor['id'] = int(time.time() * 1000)

		#event_timestamp for "now" in ISO8601-Z format
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
		wait_interval = Wait_secs_seed*generate_random_number( length=1 )
		print("**INFO: I'm going to wait here for {0} seconds.".format(wait_interval))
		time.sleep(int(wait_interval)) 

		#randomly decide if moving
		move_on = ( random.randrange(100) < Moving_chance )
		if move_on:
			
			#randomly decide where to move to, in a radius.
			print("**INFO: Let's move somewhere else.")
			current_lat, current_lon = actor["location"].split(",")
			print("**INFO:  My current location is {0},{1}".format( current_lat, current_lon ))					  
			new_location = generate_random_location( current_lat, current_lon, Radius )
			print("**INFO:  My new location will be {0}".format( new_location ) )		
			distance = calculate_distance( actor['location'], new_location )
			print("**INFO: I'm going to move {0} meters".format( distance ) )
			
			#keep track of how much I move.
			if 'route_length' in actor:
				actor['route_length'] += int(distance)
			actor['location'] = new_location
