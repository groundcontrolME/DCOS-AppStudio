#!/bin/bash

read -p "Install services? (y/n) " -n1 -s c
if [ "$c" = "y" ]; then
	echo yes
	dcos package install --yes marathon-lb
	dcos package install --yes cassandra
	dcos package install --yes kafka
	read -p "Install Elastic (requires DC/OS >= 1.9)? (y/n) " -n1 -s c1
	if [ "$c1" = "y" ]; then
		dcos package install --yes elastic
	fi
	read -p "Install Jenkins? (y/n) " -n1 -s c1	
	if [ "$c2" = "y" ]; then
		dcos package install --yes jenkins 
	fi
	echo
	read -p "Press any key when the services are started." -n1 -s 
else
	echo no
fi
echo
export CONFIGJSON='{
	"volumes": [],
	"id": "/dcos-appstudio-creator",
	"cmd": null,
	"args": null,
	"user": null,
	"env": {},
	"instances": 1,
	"cpus": 0.1,
	"mem": 256,
	"disk": 0,
	"gpus": 0,
	"executor": "",
	"constraints": [],
	"fetch": [],
	"storeUrls": [],
	"backoffSeconds": 1,
	"backoffFactor": 1.15,
	"maxLaunchDelaySeconds": 3600,
	"container": {
		"type": "DOCKER",
		"volumes": [],
		"docker": {
			"image": "fernandosanchez/appstudio:dcosappstudio-creator-v2.0.0",
			"network": "HOST",
			"portMappings": null,
			"privileged": false,
			"parameters": [],
			"forcePullImage": true
		}
	},
	"healthChecks": [
    {
      "protocol": "HTTP",
      "path": "/",
      "gracePeriodSeconds": 2,
      "intervalSeconds": 5,
      "timeoutSeconds": 2,
      "maxConsecutiveFailures": 4,
      "portIndex": 0,
      "ignoreHttp1xx": false
    }
  ],
	"readinessChecks": [],
	"dependencies": [],
	"upgradeStrategy": {
		"minimumHealthCapacity": 1,
		"maximumOverCapacity": 1
	},
	"labels": {
		"HAPROXY_GROUP": "external",
		"HAPROXY_0_VHOST": "PUBLIC_SLAVE_ELB_HOSTNAME"
	},
	"acceptedResourceRoles": null,
	"ipAddress": null,
	"residency": null,
	"secrets": {},
	"taskKillGracePeriodSeconds": null,
	"portDefinitions": [{
		"port": 10000,
		"protocol": "tcp",
		"name": "myp",
		"labels": {
			"VIP_0": "/dcosappstudiocreator:0"
		}
	}],
	"requirePorts": false
}';
echo $CONFIGJSON >config.tmp

if  [[ $1 == http* ]] 
then
	export PUBLICELBHOST=$(echo $1 | awk -F/ '{print $3}')
else
echo $1 | awk -F/ '{print $3}'
	export PUBLICELBHOST=$(echo $1 | awk -F/ '{print $1}')
fi
sed -ie "s@PUBLIC_SLAVE_ELB_HOSTNAME@$PUBLICELBHOST@g"  config.tmp
dcos marathon app add config.tmp
rm config.tmp
until $(curl --output /dev/null --silent --head --fail http://$PUBLICELBHOST); do
    printf '.'
    sleep 5
done
#open http://$PUBLICELBHOST
