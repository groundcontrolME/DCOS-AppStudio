#!/usr/bin/env python3
#
# actor.py -- actor for AppStudio geolocation demo. Simulates a moving object with a random lifespan.
#
# Author: Fernando Sanchez [ fernando at mesosphere.com ]
#
# * receives as environment variables:
# - LATITUDE 		# starting position
# - LONGITUDE 		# starting position
# - RADIUS 			# max radius of movement in meters
# - LISTENER 		# API endpoint to post updates to 
# - APPDEF 			# List-of-JSONs definition of the AppStudio environment
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
import time 				
import math

DEFAULT_LATITUDE = 40.773860
DEFAULT_LONGITUDE = -73.970813
DEFAULT_RADIUS = 300
DEFAULT_MY_ID_LENGTH = 6			#up to 1 million users - integer
DEFAULT_AGE_MAX = 60
DEFAULT_AGE_MIN = 16
DEFAULT_WAIT_SECS_SEED = 2			#every random*(THIS seconds) we consider  moving
DEFAULT_MOVING_CHANCE = 33			#chance of moving in the map
DEFAULT_SUICIDE_CHANCE = 10			#chance of commiting suicide in pct every wait time

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
	rd = float(radius) / 111300

	print("**DEBUG: generate random location with {0} m radius from {1},{2}".format(radius, latitude, longitude))

	y0 = float(latitude)
	x0 = float(longitude)

	print("**DEBUG: generate random location with {0} m radius from FLOATS {1},{2}".format(radius, y0, x0))

	u = random.uniform(0,1)
	v = random.uniform(0,1)

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
	distance_meters = R * c * 1000 # *1000 is km to m   
	print("**DEBUG: distance METERS is {0}".format(distance_meters))

	return distance_meters

if __name__ == "__main__":

	#initialize fake data factory
	fake = Faker()
	#initialize actor information
	#TODO: Actors that re-live?
	# check in Cassandra whether I exist? relaunch if I do?
	actor = {}

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

	#set my creation (birth) time as now -- remove as otherwise we'd have "extra fields"
	#actor["start_time"] = datetime.datetime.now().isoformat()[:-3]+'Z' #adapted to Zulu for Kibana

	#loop through the fields, populate
	for field in fields:

		##### CUSTOMIZE VALUES FOR KNOWN FIELDS --- To look realistic / fit to boundaries / etc
		#######################################################################################

		#search for "uuid", skip as we want a single inmutable UUID per user
		if field['name'] == "uuid":
			actor["uuid"] = generate_random_number( length=My_id_length )
			print('**DEBUG: my uuid is: {0}'.format( actor["uuid"] ) )
			print('**DEBUG: APPDEF gives me {0} but my {1} will remain at {2} as generated'.format( field['name'],field['name'],actor[field['name']] ) )
			continue

		#search for "location", if present ignore it as I'll calculate my location
		if field['name'] == "location":
			#Generate my location from lat long radius
			print("Initial location is {0},{1}".format( Latitude, Longitude ))
			actor["location"] = generate_random_location( Latitude, Longitude, Radius )
			print('**DEBUG: APPDEF gives me {0} but my {1} will remain at {2} as generated'.format( field['name'],field['name'],actor[field['name']] ) )
			continue

		#search for "route_length", if present initialize to 0 it as I'll calculate my length as I change location
		if field['name'] == "route_length":
			actor["route_length"] = 0							###### ADDED FIELD!!! MUST BE IN THE APP DEFINITION
			print('**DEBUG: APPDEF gives me {0} but my {1} will remain at {2} as generated'.format( field['name'],field['name'],actor[field['name']] ) )
			continue		

		#search for "name", if present generate one
		if field['name'] == "name":
			actor["name"] = fake.name()
			print('**DEBUG: my name is: {0}'.format( actor["name"] ) )
			continue

		#search for "age", if present generate age in range that makes sense
		if field['name'] == "age":
			actor["age"] = generate_random_number( min=Age_min, max=Age_max )
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
		#fill in the event_timestamp with "now" in javascript UTC-Zulu format
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
		commit_suicide = ( random.randrange(100) < Suicide_chance )
		#if so, (die) and exit
		if commit_suicide:
			print("**INFO: This party sucks. I'm out of here.")
			sys.exit(0)

		#wait approximate interval of change (randomized)
		#wait somewhere between 0 and 90 seconds
		wait_interval = Wait_secs_seed*generate_random_number( length=1 )
		print("**INFO: I'm going to wait here for {0} seconds.".format(wait_interval))
		time.sleep(int(wait_interval)) 

		#decide randomly whether to change or not (decide how)
		move_on = ( random.randrange(100) < Moving_chance )
		#if moving, generate new random position based on origin and radius
		if move_on:
			print("**INFO: Let's move somewhere else.")
			current_lat, current_lon = actor["location"].split(",")
			print("**INFO:  My current location is {0},{1}".format( current_lat, current_lon ))					  
			new_location = generate_random_location( current_lat, current_lon, Radius )
			print("**INFO:  My new location will be {0}, let's see how far that is from {1}".format( new_location, actor['location'] ) )		
			distance = calculate_distance( actor['location'], new_location )
			print("**INFO: I'm going to move {0} meters".format( distance ) )
			actor['route_length'] += int(distance)
			actor['location'] = new_location
