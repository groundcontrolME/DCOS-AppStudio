var express = require('express');
var router = express.Router();
var app = express();
var url= require('url');
var request = require('request');
var http = require("http");

let appjson= new String(process.env.APPDEF);
appjson= appjson.replace(/\'/g, '\"');

let appdef= JSON.parse(appjson);

let validator=process.env.VALIDATOR;
let transformer=process.env.TRANSFORMER;
let kafka= process.env.KAFKA_BACKEND;
let cassandra= process.env.CASSANDRA_BACKEND;

//transformer= "http://dcosappstudio-"+appdef.path+"workertransformer.marathon.l4lb.thisdcos.directory:0/transform";
//validator= "http://dcosappstudio-"+appdef.path+"workervalidator.marathon.l4lb.thisdcos.directory:0/validate";
//"http://dcosappstudio-"+appdef.path+"workerkafka.marathon.l4lb.thisdcos.directory:0/data";
//"http://dcosappstudio-"+appdef.path+"workercassandra.marathon.l4lb.thisdcos.directory:0/data";

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: "Listener", kafka: kafka, 
  cassandra: cassandra
    });
});

function transformMsg(msg, next) {
   console.log("Transform: "+msg);
   request.post(transformer, {form:msg}, function(err, response, body) {
    if(err== null) {
      console.log("After transform: "+body);
      validateMsg(body);
    }
    else{
      console.log("Transformation Error: "+err);
    }
  });
};

function validateMsg(msg) {
  console.log("Validate: "+msg);
   request.post(validator, {form:msg}, function(err, response, body) {
    if(err== null) {
      if(response.statusCode== 200) {
        console.log("Message validated.");
        sendToBackends(msg);
      }
      else {
        console.log("Validation Error: "+response.statusCode);
      }
    }
    else{
      console.log("Validation Error: "+err);
    }
  });
};

router.post('/data', function(req, res, next) {
 let msg= req.body;
 console.log("Msg: "+ JSON.stringify(msg));
 msg= transformMsg(msg);
 res.statusCode= 200;
 res.end();
});

function sendToKafka(msg) {
  request.post(kafka, {form:msg}, function(err, response, body) {
    if(err) {
      console.log("Kafka: "+err);
    }
    else {
      console.log("Kafka statusCode: "+response.statusCode);
    }
});
};

function sendToCassandra(msg) {
  request.post(cassandra, {form:msg}, function(err, response, body) {
    if(err) {
      console.log("Cassandra: "+err);
    }
    else {
     console.log("Cassandra statusCode: "+response.statusCode);
    }
});
};

function sendToBackends(msg) {
    console.log("Sending to Kafka: "+msg);
    sendToKafka(JSON.parse(msg));
    console.log("Sending to Cassandra: "+msg);
    sendToCassandra(JSON.parse(msg));

    // Elastic Integration
    console.log("Sending to Elastic: "+msg);
    sendToElastic(JSON.parse(msg));
}

function sendToElastic(msg) {
  request.post(process.env.ELASTIC_BACKEND, {form:JSON.stringify(msg)}, function(err, response, body) {
    if(err) {
      console.log("Elastic: "+err);
    }
    else {
     console.log("Elastic statusCode: "+response.statusCode);
    }
});
};

module.exports = router;


