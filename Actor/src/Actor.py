#!/usr/bin/env python3

# actor.py -- actor for AppStudio geolocation demo. Simulates a moving object with a lifespan.
# * receives as environment variables:
# - LATITUDE 		# starting position
# - LONGITUDE 		# starting position
# - RADIUS 			# max radius of movement in meters
# - LISTENER 		# API endpoint to post updates to 
# - APPDEF 			# List-of-JSONs definition of the AppStudio environment 
# * Other factors as constants:
# - WAIT_SECS_SEED	# order of magnitude in seconds of period after which we consider change or die
# - MOVING_CHANCE 	# % probability of position change each WAIT_SECS_SEED seconds
# - SUICIDE_CHANCE	# % probability of exiting each WAIT_SECS_SEED seconds
# * Not currently used:
# - amount of change in meters (speed-like)	# use "RADIUS"
# - duration/lifespan						# use "SUICIDE_CHANCE"


#load environment variables
import sys
import os
import requests
import json
import random
from faker import Faker		#fake-factory: generates good-looking random data
import datetime
import time 				#required to generate JS-style datetime for msg id
import math

DEFAULT_LATITUDE = 41.411338
DEFAULT_LONGITUDE = 2.226438
DEFAULT_RADIUS = 300
MY_ID_LENGTH = 6			#up to 1 million users - integer
AGE_MAX = 60
AGE_MIN = 16
WAIT_SECS_SEED = 2			#every random*(10 seconds) we thing of moving
SUICIDE_CHANCE = 10			#chance of commiting suicide in pct every wait time
MOVING_CHANCE = 33			#chance of moving in the map

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
	field is {"name": name, "type": JStype, "pivot": boolean}
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
	"""
	rd = int(radius) / 111300

	print("**DEBUG: generate random location with {0} m radius from {1},{2}".format(radius, latitude, longitude))

	y0 = float(latitude)
	x0 = float(longitude)

	print("**DEBUG: generate random location with {0} m radius from FLOATS {1},{2}".format(radius, y0, x0))

	u = float(generate_random_number( length=5 ))
	v = float(generate_random_number( length=5 ))

	print("**DEBUG: seeds are {0} and {1}".format( u, v ) )

	w = rd*math.sqrt(u)
	t = 2*math.pi*v
	x = w*math.cos(t)
	y = w*math.sin(t)

	new_location = str(y+y0)+","+str(x+x0)
	print('**DEBUG: new_location is {0}'.format(new_location))

	return new_location

def calculate_distance (src_coords, dst_coords):
	"""
	#Calculates the distance in meters between two coordinates.
	#These are received as a string with "lat,long".
	"""

	R = 6373.0	#earth radius in km

	print("**DEBUG: received src {0} and dst {1}".format(src_coords, dst_coords))
	lat1, lon1 = src_coords.split(',')
	print("**DEBUG: find src coords : lat is {0} long is {1}".format(lat1, lon1))
	lat2, lon2 = dst_coords.split(',')
	print("**DEBUG: find dst coords : lat is {0} long is {1}".format(lat2, lon2))
	#this fails lat1, lon1, lat2, lon2 = map(float(), (lat1,lon1,lat2,lon2))
	lat1 = float(lat1)
	lon1 = float(lon1)
	lat2 = float(lat2)
	lon2 = float(lon2)
	print("**DEBUG: coords in floats are src: {0},{1} | dst: {2},{3}".format(lat1, lon1, lat2, lon2))

	# convert decimal degrees to radians 
	lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
	#lat1 = math.radians(float(lat1))
	#lon1 = math.radians(float(lon1))
	#lat2 = math.radians(float(lat2))
	#lon2 = math.radians(float(lon2))
	print("**DEBUG: coords in radians are: src is {0},{1} | dst is {2} {3}".format(lat1, lon1, lat2, lon2))

	# haversine formula 
	dlon = lon2 - lon1 
	dlat = lat2 - lat1 
	a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
	c = 2 * math.asin(math.sqrt(a)) 
	distance_meters = R * c * 1000   

	print("**DEBUG: distance METERS is {0}".format(distance_meters))
	return distance_meters

if __name__ == "__main__":

	#initialize fake data factory
	fake = Faker()
	#initialize actor information
	#TODO: check in Cassandra whether I exist? relaunch if I do?
	actor = {}

	# Parse environment variables
	latitude = os.getenv('LATITUDE', DEFAULT_LATITUDE)
	longitude = os.getenv('LONGITUDE', DEFAULT_LONGITUDE)
	radius = os.getenv('RADIUS', DEFAULT_RADIUS)
	#Listener POST endpoint is an environment variable
	listener = os.getenv('LISTENER')
	print('**DEBUG: Listener is: {0}'.format( listener ) )

	# Read fields from env variable APPDEF
	appdef_env = os.getenv('APPDEF', {} )
	print('**APPDEF is: {0}'.format( appdef_env ) )
	if appdef_env:
		appdef_clean = appdef_env.replace( "'", '"' )	#[:-1] has happened that the last char is rubbish
		print('**APPDEF clean is: {0}'.format( appdef_clean ) )
		appdef = json.loads(appdef_clean)
		fields = appdef['fields']
	else:
		appdef_clean = ""
		fields = []
	#Generate my location from lat long radius
	actor["location"] = generate_random_location( latitude, longitude, radius )

	##### ADD SPECIFIC FIELDS --- These NEED to be added to the app definition / schema or Validation will fail!
	##### MANDATORY FOR APP DEFINITION! #############
	############################################################################################################
	# Generate my ID - 13 figures number
	my_id = generate_random_number( length=MY_ID_LENGTH )
	# initially use 'uuid' as per fixed schema
	# my_id = datetime.datetime.now().isoformat()
	print('**DEBUG: my id is: {0}'.format( my_id ) )
	actor["uuid"] = my_id 								###### ADDED FIELD!!! MUST BE IN THE APP DEFINITION
	#I haven't moved so route_length is 0
	actor["route_length"] = 0							###### ADDED FIELD!!! MUST BE IN THE APP DEFINITION
	#set my creation (birth) time as now
	#actor["start_time"] = datetime.datetime.now().isoformat()[:-3]+'Z' #adapted to Zulu for Kibana

	#loop through the fields, populate
	for field in fields:

		##### SPECIFIC FIELDS --- These are already added, not from APPDEF
		####################################################################
		#search for "uuid", skip as we want a single inmutable UUID per user
		if field['name'] == "uuid":
			print('**DEBUG: APPDEF gives me {0} but my {1} will remain at {2} as generated'.format( field['name'],field['name'],actor[field['name']] ) )
			continue

		#search for "route_length", if present ignore it as I'll calculate my length
		if field['name'] == "route_length":
			print('**DEBUG: APPDEF gives me {0} but my {1} will remain at {2} as generated'.format( field['name'],field['name'],actor[field['name']] ) )
			continue	

		#search for "location", if present ignore it as I'll calculate my location
		if field['name'] == "location":
			print('**DEBUG: APPDEF gives me {0} but my {1} will remain at {2} as generated'.format( field['name'],field['name'],actor[field['name']] ) )
			continue	

		##### CUSTOMIZE VALUES FOR KNOWN FIELDS --- To look realistic / fit to boundaries / etc
		#######################################################################################
		#search for "name", if present generate one
		if field['name'] == "name":
			actor["name"] = fake.name()
			print('**DEBUG: my name is: {0}'.format( actor["name"] ) )
			continue

		#search for "age", if present generate age in range that makes sense
		if field['name'] == "age":
			actor["age"] = generate_random_number( min=AGE_MIN, max=AGE_MAX )
			print('**DEBUG: my age is: {0}'.format( actor["age"] ) )
			continue

		#search for "country", if present generate a country name
		if field['name'] == "country":
			actor["country"] = fake.country()
			print('**DEBUG: my country is: {0}'.format( actor["country"] ) )
			continue

		#field is LEARNED from APPDEF, fill it with gibberish
		actor[field['name']] = get_random_for_type( field )
		print('**DEBUG: LEARNED field: {0} | generated value: {1}'.format( field['name'], actor[field['name']] ) )

	#### All fields are now ready, start posting
	while True:

		##### MANDATORY FIELDS 
		#fill in the message Id with "now" in javascript/unixtime format. TODO: make it *really* unique
		actor['id'] = int(time.time() * 1000)
		#fill in the event_timestamp with "now" in javascript format
		temp_date = datetime.datetime.utcnow().isoformat()	#Needs to be ISO8601 as in "2017-04-26T07:05:00.91Z"
		timestamp_8601_Z = temp_date[:-3]+'Z'
		print('**DEBUG: event_timestamp is: {0}'.format( timestamp_8601_Z ) )
		actor['event_timestamp'] = timestamp_8601_Z
		#Position is updated above and below
		print('**DEBUG: ACTOR is: {0}'.format( actor ) )
		#build the request
		headers = {
		'Content-type': 'application/json'
		}
		#send the message with "actor"
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

		#decide whether I die based on creation time and and duration/lifespan
		#TODO: for now we'll just give him a % chance of being alive
		commit_suicide = ( random.randrange(100) < SUICIDE_CHANCE )
		#if so, (die) and exit
		if commit_suicide:
			print("**INFO: This party sucks. I'm out of here.")
			sys.exit(0)

		#wait approximate interval of change (randomized)
		#wait somewhere between 0 and 90 seconds
		wait_interval = WAIT_SECS_SEED*generate_random_number( length=1 )
		print("**INFO: I'm going to wait here for {0} seconds.".format(wait_interval))
		time.sleep(int(wait_interval)) 

		#decide randomly whether to change or not (decide how)
		move_on = ( random.randrange(100) < MOVING_CHANCE )
		#if moving, generate new random position based on origin and radius
		if move_on:
			print("**INFO: Let's move somewhere else.")
			new_location = generate_random_location( latitude, longitude, radius )
			print("**INFO:  My new location will be {0}, let's see how far that is from {1}".format( new_location, actor['location'] ) )		
			distance = calculate_distance( actor['location'], new_location )
			print("**INFO: I'm going to move {0} meters".format( distance ) )
			actor['route_length'] += int(distance)
			actor['location'] = new_location
