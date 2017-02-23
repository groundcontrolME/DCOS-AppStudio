var express = require('express');
var router = express.Router();
var url= require('url');
var request = require('request');
var http = require("http");

let json= new String(process.env.APPDEF);
json= json.replace(/\'/g, '\"');

let appdef= JSON.parse(json);

let fields= new Array(); 
let types= new Array();

for(var i= 0; i< appdef.fields.length; i++) {
  fields[i] = appdef.fields[i].name;
  types[i] = appdef.fields[i].type;
}

let elastic= process.env.ELASTIC_SERVICE;

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: "Elastic Worker", appdef: JSON.stringify(appdef)
    });
});

let index= { "mappings": { "event_timestamp": { "properties": { "event_timestamp": { "type": "date" }}}, "location": { "properties": { "location": { "type": "geo_point" }}}, "heartrate": { "properties": { "heartrate": { "type": "integer" }}}, "user": { "properties": { "user": { "type": "string" }}}, "deviceid": { "properties": { "deviceid": { "type": "string" }}}, "color": { "properties": { "color": { "type": "string" }}}}}

let ni= 0;
// Create index  
try {
    let props= '{ "mappings": { "event_timestamp": { "properties": { "event_timestamp": { "type": "date" }}}, "location": { "properties": { "location": { "type": "geo_point" }}}';
    for(var i= 0; i< fields.length; i++) {
      if(fields[i]=== "id" || fields[i]=== "event_timestamp" || fields[i]=== "location")
        continue;
      if(i< fields.length-1) {
        props+= ", "
      }
      let type= "integer";
      if(types[i]=== "Long")
        type= "long";
      if(types[i]=== "Double")
        type= "double";
      if(types[i]=== "Boolean")
        type= "boolean";
      if(types[i]=== "String")
        type= "string";
      if(types[i]=== "Date/time" || types[i]=== "Date/Time")
        type= "date";
      if(types[i]=== "Location")
        type= "geo_point";

      props+= '"'+fields[i]+'": { "properties": { "'+fields[i]+'": { "type": "'+type+'" }}}';
    }
    props+="}}";
    console.log("Elastic Index: "+props);
    console.log("Elastic: "+elastic+"/"+appdef.path+"?pretty");
    
    createIndex(props);
}
catch(ex) {
  console.log(ex);
}

function createIndex(props) {
  request.put(elastic+"/"+appdef.path+"?pretty", {form: props}, function(err, response, body) {
      if(err== null) {
        console.log(body);
      }
      else {
        console.log(ni+" "+err);
      }
      if(response.statusCode == 404) {
        if(ni< 32) {
            ni++;
            setTimeout(createIndex(props), 100);
         }
      }
    });
};

function putToElastic(json, id) {
  try {
    console.log("Put to elastic: "+elastic+"/"+appdef.path+"/external/"+id+"?pretty");
    request.put(elastic+"/"+appdef.path+"/external/"+id+"?pretty", {form:JSON.stringify(json)}, function(err, response, body) {
      if(err== null) {
        console.log(body);
      }
      else {
        console.log(err);
      }
    });
  }
  catch(ex) {
    console.log(ex);    
  }
};



router.post('/data', function(req, res, next) {
  console.log(req.body);
  let json= JSON.parse(req.body);
  let t= json.event_timestamp;
  let ms= new Date(t.toString().trim()).getTime();
  json.event_timestamp= ms;
  console.log("ms: "+ms);
  console.log("json: "+JSON.stringify(json));
  let id= json.id;
  delete json.id;
  putToElastic(json, id);
  res.statusCode= 200;
  res.end();
});

module.exports = router;
