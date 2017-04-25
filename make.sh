#!/bin/bash

export DOCKERHUB_USER=fernandosanchez
export DOCKERHUB_REPO=appstudio
export DOCKERHUB_PASSWD=$1
export VERSION=2.0.0
export BASEIMAGE=node694
export APP_DIR=opt/app
export LOCATION="'"'{ "latitude":41.41187, "longitude":-2.22589 }'"'"

export CREATOR_APP_DIR=$(PWD)"/CreatorApp"
export GROUP_JSON=$CREATOR_APP_DIR"/groupconfig-v"$VERSION".json"
export INSTALLER=$CREATOR_APP_DIR"/install-dcos-appstudio.sh"


#check command-line arguments
if [[ $# < 1 ]]; then
	echo "Usage: make.sh [Docker Hub password]"
	exit 1
fi

cp -r versions/$VERSION/* .
echo copy done
docker login -u $DOCKERHUB_USER -p $DOCKERHUB_PASSWD
echo login done

#Generate dockerfile with docker hub info 
sudo cat > Dockerfile  << EOF
FROM ${DOCKERHUB_USER}/${DOCKERHUB_REPO}:${BASEIMAGE}

COPY . /$APP_DIR
ENV APPDIR=$APP_DIR
ENV MESOS_SANDBOX=/$APP_DIR
ENTRYPOINT /opt/node/bin/node /$APP_DIR/bin/www
EOF

#configure group JSON for CreatorApp
cp $GROUP_JSON.TEMPLATE $GROUP_JSON
sed -i -- "s,__DOCKERHUB_USER__,$DOCKERHUB_USER,g" $GROUP_JSON
sed -i -- "s,__DOCKERHUB_REPO__,$DOCKERHUB_REPO,g" $GROUP_JSON
sed -i -- "s,__VERSION__,$VERSION,g" $GROUP_JSON
sed -i -- "s,__LOCATION__,$LOCATION,g" $GROUP_JSON  #Pass #LOCATION as an environment variable to Creator only if defined

#configure appstudio installer
cp $INSTALLER.TEMPLATE $INSTALLER
sed -i -- "s,__DOCKERHUB_USER__,$DOCKERHUB_USER,g" $INSTALLER
sed -i -- "s,__DOCKERHUB_REPO__,$DOCKERHUB_REPO,g" $INSTALLER
sed -i -- "s,__VERSION__,$VERSION,g" $INSTALLER


if [[ $VERSION == 1.0.0 ]] 
then
	cp Dockerfile CreatorApp
	cd CreatorApp
	docker build -t $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-creator-v$VERSION .
	docker push $DOCKERHUB_USER/$DOCKERHUB_REPO:dcosappstudio-creator-v$VERSION 
	cd ..
fi

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
