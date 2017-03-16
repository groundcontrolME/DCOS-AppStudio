var express = require('express');
var router = express.Router();
var app = express();
var url= require('url');
var request = require('request');
var http = require("http");
var yamlParser= require('yamljs');
var Fiber = require('fibers');
var parseString = require('xml2js').parseString;
var xmlasjson;

var globals= new Object();

function fiberparseXML(xml, ret) {
    var fiber = Fiber.current;
    parseString(xml, function (err, result) {
      xmlasjson= result;
  });
  Fiber.yield();
};


function parseXML(xml) {
  let ret= "";
Fiber(function() {
  console.log("! "+xml)
    fiberparseXML(xml, ret);
}).run();
  return xmlasjson;
};

let appjson= new String(process.env.APPDEF);
appjson= appjson.replace(/\'/g, '\"');

let appdef= JSON.parse(appjson);

let transformer= decodeURIComponent(appdef.transformer);
console.log("transformer: "+ transformer);

let fields= new Array(); 
let types= new Array()
let typesByName= new Object();

for(var i= 0; i< appdef.fields.length; i++) {
  fields[i] = appdef.fields[i].name;
  types[i] = appdef.fields[i].type;
  typesByName[fields[i]]= types[i];
}

var rawtext;
var result;

function doTransform(req, res, next) {
  try {
  rawtext= req.body;
  result= rawtext;
  console.log("received msg: "+rawtext);
console.log(transformer);
  eval("try {"+transformer+"} catch (ex) { console.log(ex)}");
  if(result== null)
    throw "result== null";
  console.log("Transformed msg: "+result);
  res.write(result);
  res.statusCode= 200;
  }
  catch(ex) {
    res.statusCode= 400;
  }
  res.end();
};

router.get('/transform', doTransform);
router.post('/transform', doTransform);

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: "Message Transformer"});
});

module.exports = router;


