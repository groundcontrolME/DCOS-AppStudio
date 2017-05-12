#!/bin/bash

export DOCKERHUB_USER=fernandosanchez
export DOCKERHUB_REPO=appstudio
export VERSION=2.0.0

#Creator location and template files
export CREATOR_APP_DIR=$(PWD)"/CreatorApp"
export GROUP_JSON=$CREATOR_APP_DIR"/groupconfig-v"$VERSION".json"
export INSTALLER=$CREATOR_APP_DIR"/install-dcos-appstudio.sh"

#Node/JS apps defaults
export BASEIMAGE=node694
export APP_DIR=opt/app

#Python apps defaults
export APPS_PY="actor"			#this will be a LIST with other modules/apps, space separated
export APP_DIR_PY="src"			#where the code lives
export BASEIMAGE_PY=alpine-python3
export REQUIREMENTS_PY=requirements.txt

#defaults
export LATITUDE="38.220107"		#coords for event generation 
export LONGITUDE="-122.279448"		#SF bay
export RADIUS="1000"			#radius of events in meters	
export ROUTES_URI="https://raw.githubusercontent.com/fernandosanchezmunoz/DCOS-AppStudio/master/actor/routes/routes.csv"

#check command-line arguments
if [[ $# < 1 ]]; then
	echo "Enter your dockerhub password for the account $DOCKERHUB_USER: "
	read -s DOCKERHUB_PASSWD
fi

cp -r versions/$VERSION/* .
echo copy done
docker login -u $DOCKERHUB_USER -p $DOCKERHUB_PASSWD
echo login done

# Python apps section
############################################

for i in $APPS_PY; do
	#Python apps: export variables
	echo "**DEBUG: export vars for app "$i
	export THIS_DIR=$(PWD)"/"$i
	echo "**DEBUG: app_dir is "$THIS_DIR	
	echo "**DEBUG: create dockerfile for app "$i	

	#create Dockerfile
	cat > $THIS_DIR/Dockerfile  << EOF
FROM ${DOCKERHUB_USER}/${DOCKERHUB_REPO}:${BASEIMAGE_PY}

RUN mkdir -p $APP_DIR_PY
COPY ./$APP_DIR_PY/* ./
RUN pip install -r requirements.txt
ENTRYPOINT python3 -u $i.py
EOF

	#build and push
	echo "**DEBUG: build and push app "$i
	cd $THIS_DIR	
	echo "**INFO: building and pushing "$DOCKERHUB_USER/$DOCKERHUB_REPO":dcosappstudio-"$i"-v"$VERSION
	docker build -t $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-$i-v$VERSION .
	docker push $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-$i-v$VERSION
        echo "**INFO: finished building and pushing "$DOCKERHUB_USER/$DOCKERHUB_REPO":dcosappstudio-"$i"-v"$VERSION
	cd ..

done #Python apps

#Common to Python and Node/JS apps: 
##############################################

#configure group JSON for CreatorApp
cp $GROUP_JSON.TEMPLATE $GROUP_JSON
sed -i '' "s,__DOCKERHUB_USER__,$DOCKERHUB_USER,g" $GROUP_JSON
sed -i '' "s,__DOCKERHUB_REPO__,$DOCKERHUB_REPO,g" $GROUP_JSON
sed -i '' "s,__VERSION__,$VERSION,g" $GROUP_JSON
sed -i '' "s,__LATITUDE__,$LATITUDE,g" $GROUP_JSON
sed -i '' "s,__LONGITUDE__,$LONGITUDE,g" $GROUP_JSON
sed -i '' "s,__RADIUS__,$RADIUS,g" $GROUP_JSON
sed -i '' "s,__ROUTES_URI__,$ROUTES_URI,g" $GROUP_JSON


#configure appstudio installer
cp $INSTALLER.TEMPLATE $INSTALLER
sed -i '' "s,__DOCKERHUB_USER__,$DOCKERHUB_USER,g" $INSTALLER
sed -i '' "s,__DOCKERHUB_REPO__,$DOCKERHUB_REPO,g" $INSTALLER
sed -i '' "s,__VERSION__,$VERSION,g" $INSTALLER

# Node/JS apps section
############################################

#JS/node: Generate dockerfile with docker hub info 
cat > Dockerfile  << EOF
FROM ${DOCKERHUB_USER}/${DOCKERHUB_REPO}:${BASEIMAGE}

COPY . /$APP_DIR
ENV APPDIR=$APP_DIR
ENV MESOS_SANDBOX=/$APP_DIR
ENTRYPOINT /opt/node/bin/node /$APP_DIR/bin/www
EOF
	
cp Dockerfile CreatorApp
cd CreatorApp
docker build -t $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-creator-v$VERSION .
docker push $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-creator-v$VERSION 
	cd ..

if [[ $VERSION == 2.0.0 ]] 
then
	cp Dockerfile WorkerElasticApp
	cd WorkerElasticApp
	docker build -t $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-elasticingester-v$VERSION .
	docker push $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-elasticingester-v$VERSION
	cd ..
fi

cp Dockerfile WorkerCassandraApp
cd WorkerCassandraApp
docker build -t $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-cassandraingester-v$VERSION .
docker push $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-cassandraingester-v$VERSION 
cd ..

cp Dockerfile WorkerKafkaApp
cd WorkerKafkaApp
docker build -t $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-kafkaingester-v$VERSION .
docker push $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-kafkaingester-v$VERSION 
cd ..

cp Dockerfile MessageTransformerApp
cd MessageTransformerApp
docker build -t $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-messagetransformer-v$VERSION .
docker push $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-messagetransformer-v$VERSION 
cd ..

cp Dockerfile MessageValidatorApp
cd MessageValidatorApp
docker build -t $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-messagevalidator-v$VERSION .
docker push $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-messagevalidator-v$VERSION 
cd ..

cp Dockerfile WorkerListenerApp
cd WorkerListenerApp
docker build -t $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-messagelistener-v$VERSION .
docker push $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-messagelistener-v$VERSION 
cd ..

cp Dockerfile UI		
cd UI
docker build -t $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-ui-v$VERSION .
docker push $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-ui-v$VERSION 
cd ..

cp Dockerfile WorkerLoadGeneratorApp
cd WorkerLoadGeneratorApp
docker build -t $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-loader-v$VERSION .
docker push $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-loader-v$VERSION 
cd ..
