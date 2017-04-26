#!/usr/bin/env python3

# actor.py -- actor for AppStudio geolocation demo. Simulates a moving object with a lifespan.
# receives as environment variables:
# - original position 
# - radius of movement
# - approximate interval of position change
# - amount of change in meters (speed-like)
# - duration/lifespan
# - listener API endpoint

#load environment variables
import sys
import os
import requests
import json
import random
from faker import Faker	#fake-factory: generates good-looking random data
import datetime
import time 				#required to generate JS-style datetime for msg id
import math

DEFAULT_LATITUDE = 41.411338
DEFAULT_LONGITUDE = 2.226438
DEFAULT_RADIUS = 300
MY_ID_LENGTH = 13
AGE_MAX = 60
AGE_MIN = 16
WAIT_SECS_SEED = 10			#every random*(10 seconds) we thing of moving
SUICIDE_CHANCE = 3			#chance of commiting suicide in pct every wait time
MOVING_CHANCE = 30			#chance of moving in the map

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

def get_random_for_type( my_type ):
	"""
	Generates a random value for the type received.
	Type is a JS type defined by the app, not a python type.
	"""

	print('**DEBUG: my_type is of type is {0}'.format(my_type))

	if my_type == "String": return fake.bs() 
	if my_type == "Integer": return generate_random_number( length=generate_random_number( length=3 ) )		
	if my_type == "Long": return generate_random_number( generate_random_number( length=7 ) )							
	if my_type == "Double": return generate_random_number( min=(-1)*generate_random_number( length=7 ) , \
							max=generate_random_number( length=7 ) )			
	if my_type == "Location": return str(fake.latitude())+","+str(fake.longitude()) 
	if ( my_type == "Date/time" or my_type == "Date/Time" ): return str(fake.date_time()) 

	print('**ERROR: my_type is not detected')
	return None

def generate_random_location( latitude, longitude, radius ):
	"""
	Generates a random location from lat, long, radius
	returns in as string in "latitude", "longitude" format.
	"""
	rd = int(radius) / 111300

	u = float(generate_random_number(length=7))
	v = float(generate_random_number(length=7))

	w = rd*math.sqrt(u)
	t = 2*math.pi*v
	x = w*math.cos(t)
	y = w*math.sin(t)

	new_location = str(y+float(latitude))+","+str(x+float(longitude))
	print('**DEBUG: new_location is {0}'.format(new_location))

	return new_location

if __name__ == "__main__":

	#initialize fake data factory
	fake = Faker()
	#initialize actor information
	actor = {}

	# Parse environment variables
	latitude = os.getenv('LATITUDE', DEFAULT_LATITUDE)
	longitude = os.getenv('LONGITUDE', DEFAULT_LONGITUDE)
	radius = os.getenv('RADIUS', DEFAULT_RADIUS)
	#Listener POST endpoint is an environment variable
	listener = os.getenv('LISTENER')
	print('**DEBUG Listener is: {0}'.format( listener ) )

	# Read fields from env variable APPDEF
	appdef_env = os.getenv('APPDEF', {} )
	print('**APPDEF is: {0}'.format( appdef_env ) )
	appdef_clean = appdef_env.replace( "'", '"' )[:-1]
	print('**APPDEF clean is: {0}'.format( appdef_clean ) )
	appdef = json.loads(appdef_clean)
	fields = appdef['fields']

	#Generate my location from lat long radius
	actor["location"] = generate_random_location( latitude, longitude, radius )

	# Generate my ID - 13 figures number
	my_id = generate_random_number( length=MY_ID_LENGTH )
	print('**DEBUG my id is: {0}'.format( my_id ) )
	actor["uuid"] = my_id

	#loop through the fields, populate
	for field in fields:
		#search for "name", if present generate one
		if field['name'] == "name":
			actor["name"] = fake.name()
			print('**DEBUG my name is: {0}'.format( my_age ) )
			continue

		#search for "age", if present generate age in range that makes sense
		if field['name'] == "age":
			actor["age"] = generate_random_number( min=AGE_MIN, max=AGE_MAX )
			print('**DEBUG my age is: {0}'.format( my_age ) )
			continue

		#search for "country", if present generate a country name
		if field['name'] == "country":
			actor["country"] = fake.country()
			print('**DEBUG my country is: {0}'.format( my_country ) )
			continue

		#field is not well-known, fill it with gibberish
		actor[field['name']] = get_random_for_type( field['type'] )

	# NOT USED:
	# Kafka topic
	# Cassandra keyspace
	# Cassandra table
	# creator API endpoint

	#set my creation (birth) time as now
	actor["start_time"] = datetime.datetime.now().strftime("%I:%M%p %B %d, %Y")

	#### All fields are now ready, start posting
	while True:

		#fill in the message Id with "now" in javascript format
		actor['id'] = int(time.time() * 1000)
		print('**DEBUG ACTOR is: {0}'.format( actor ) )
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
			print("** INFO: sent update: \n{0}".format(actor))
		except (
		    requests.exceptions.ConnectionError ,\
		    requests.exceptions.Timeout ,\
		    requests.exceptions.TooManyRedirects ,\
		    requests.exceptions.RequestException ,\
		    ConnectionRefusedError
		    ) as error:
			print ('** ERROR: update failed {}: {}'.format( actor, error ) ) 

		#decide whether I die based on creation time and and duration/lifespan
		#TODO: for now we'll just give him a % chance of being alive
		commit_suicide = ( random.randrange(100) < SUICIDE_CHANCE )
		#if so, (die) and exit
		if commit_suicide:
			print("** This party sucks. I'm out of here.")
			sys.exit(0)

		#wait approximate interval of change (randomized)
		#wait somewhere between 0 and 90 seconds
		wait_interval = WAIT_SECS_SEED*generate_random_number( length=1 ) 

		#decide randomly whether to change or not (decide how)
		move_on = ( random.randrange(100) < MOVING_CHANCE )
		#if moving, generate new random position based on origin and radius
		if move_on:
			print("** Let's move somewhere else.")
			actor['location'] = generate_random_location( latitude, longitude, radius )
