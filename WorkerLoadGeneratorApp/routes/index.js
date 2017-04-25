var express = require('express');
var router = express.Router();
var app = express();
var url= require('url');
var request = require('request');
var location = process.env.LOCATION;
// { "latitude": 41.41187, "longitude": -2.22589 }
var radius_meters = 1000

let listener= process.env.LISTENER;

let json= new String(process.env.APPDEF);
json= json.replace(/\'/g, '\"');
let appdef= JSON.parse(json);
let fields= new Array(); 
let types= new Array();

for(var i= 0; i< appdef.fields.length; i++) {
 // console.log(JSON.stringify(appdef.fields));
  fields[i] = appdef.fields[i].name;
  types[i] = appdef.fields[i].type;
}
//console.log(JSON.stringify(fields));

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: "Loader", nmsg: n});
});

let n= 0;
const fs = require('fs');
let warandpeace;
let length;
let lines= new Array();
let nl= 0;
let sentlines= 0;
let fisjson= false;

function readDataFile() {
  console.log("Reading file...");
var lineReader = require('readline').createInterface({
  input: require('fs').createReadStream(process.env.APPDIR+"/public/"+appdef.fname)
});

  lineReader.on('line', function (line) {
  if(line.length== 0)
    return;
    console.log("Line: "+line);
  if(nl== 0) {
    try {
      let jl= JSON.parse(line);
      fisjson= true;
    }
    catch(ex) {
      fisjson= false;
    }
  }
  lines[nl++]= line;
});

lineReader.on('close', function() {
setTimeout(loadFromFile, Math.floor(1000/appdef.frequency));  
  console.log("Lastline read... "+Math.floor(1000/appdef.frequency));

});

};

if(appdef.byod=== "yes") {
  let f= process.env.DATASERVICE+"/"+appdef.fname;
  console.log("Trying to download: "+f);
  request.head(process.env.DATASERVICE+"/"+appdef.fname, function(err, res, body){
    if(err) {
      console.log("INFO: Can't download data file.");
    }
    else {
       console.log('content-type:', res.headers['content-type']);
       console.log('content-length:', res.headers['content-length']);
       request(f).pipe(fs.createWriteStream(process.env.APPDIR+"/public/"+appdef.fname)).on('close', readDataFile);
  }
});
}
else {
console.log("Reading: "+process.env.APPDIR+"/warandpeace.txt");
fs.readFile(process.env.APPDIR+"/warandpeace.txt", 'utf8', function(err, data) {
  if (err) throw err;
  warandpeace= new String(data);
  length= warandpeace.length;
});

console.log("Reading: "+process.env.APPDIR+"/airports.txt");
fs.readFile(process.env.APPDIR+"/airports.txt", 'utf8', function(err, data) {
  if (err) throw err;
  airports= new String(data).split("\n");
  console.log(airports[0]);
  console.log(airports[1]);
  
  console.log(airports[6976]);
  console.log(airports[6977]);
  
});
}

function getPseudoRandomGeo(center, radius) {
    var y0 = center.latitude;
    var x0 = center.longitude;
    var rd = radius / 111300;

    var u = Math.random();
    var v = Math.random();

    var w = rd * Math.sqrt(u);
    var t = 2 * Math.PI * v;
    var x = w * Math.cos(t);
    var y = w * Math.sin(t);

    // var xp = x / Math.cos(y0);
    result = {
        'latitude': y + y0,
        'longitude': x + x0
    };
    console.log("**DEBUG: Result is: "+JSON.stringify(result));     

    return result
};

function getRandomLocation() {
  //let a= airports[Math.floor(Math.random() * 6977)];
  //let splits= a.split(",");
  geo = getPseudoRandomGeo(location, radius_meters);
  console.log("**DEBUG: Geo is " + geo);  
  formattedGeo = geo['latitude']+","+geo['longitude'];
  console.log("**DEBUG: Formatted Geo is " + formattedGeo);
  return formattedGeo;
};

function getRandomInt() {
  return Math.floor(Math.random() * 101);
};

function getRandomLong() {
  return Math.floor(Math.random() * 10001);
};

function getRandomFloat() {
  return (Math.random() * 1000001);
};

function getRandomBoolean() {
  if(Math.random()> 0.5)
    return true;
  return false;
};

function getRandomDateTime() {
  let now= new Date().getTime();
  let d= new Date(now - Math.floor(Math.random()*1000*100000*14));
  let day= d.getUTCDate();
			let daystring= ""+day;
			
  			if(day< 10)
    				daystring="0"+daystring;
  			let month= d.getUTCMonth()+1;
  			let monthstring= ""+month;
  			if(month< 10)
    				monthstring="0"+monthstring;
            		
		        let hour= d.getUTCHours();
			let hourstring= ""+hour;
  			if(hour< 10)
    				hourstring="0"+hourstring;
            		
			let minute= d.getUTCMinutes();
			let minutestring= ""+minute;
  			if(minute< 10)
    				minutestring="0"+minutestring;
            		    
			let second= d.getUTCMilliseconds()/1000.0;
			let secondstring= ""+second;
  			if(second< 10)
    				secondstring="0"+secondstring
			    

  return d.getFullYear()+"-"+monthstring+"-"+daystring+"T"+hourstring+":"+minutestring+":"+secondstring+"Z";
};

function getRandomString() {
  let start= Math.floor(Math.random() * (length- 128* Math.random()));
  let words= Math.floor((Math.random() * 10) + 1);

  while(warandpeace.charAt(start)!= ' ' && warandpeace.charAt(start)!= ".") {
    start++;
  }
  start++;
  let end= start+1;
  for(var i= 0; i< words; i++) {
    while(warandpeace.charAt(end)!= ' ' && warandpeace.charAt(start)!= ".") {
      end++;
    }
    end++;
  }
  let ret= warandpeace.substring(start, end);
  ret= ret.replace(/\n/g, '');
  ret= ret.replace(/,/g, ' ');
  ret= ret.replace(/:/g, ' ');
  ret= ret.replace(/"/g, ' ');
  ret= ret.replace(/'/g, ' ');
  ret= ret.replace(/!/g, ' ');
  ret= ret.replace(/\(/g, ' ');
  ret= ret.replace(/\)/g, ' ');
  ret= ret.replace(/\?/g, ' ');
  ret= ret.replace(/\./g, ' ');
  return ret;
};

function getRandomForType(t) {
  if(t === "String") 
    return getRandomString();
  if(t === "Integer") 
    return getRandomInt();
  if(t === "Long") 
    return getRandomLong();
  if(t === "Double") 
    return getRandomFloat();
  if(t === "Boolean") 
    return (Math.random()>0.5)?true:false;
  if(t === "Date/Time" || t === "Date/time") 
    return getRandomDateTime();
  if(t === "Location") 
    return getRandomLocation();
};

 

if(!(appdef.byod=== "yes")) {
  setTimeout(load, 1000);
}


function loadFromFile() {
  let thisline;
  if(fisjson) {
    thisline= lines[sentlines];
  }
  else {
   // console.log
    let csv= lines[sentlines];
    let splits= csv.split(";");
    thisline= "{";
    for(var i= 0; i< appdef.fields.length; i++) {
      thisline+= '"'+fields[i]+'":"'+splits[i]+'"';
      if(i< appdef.fields.length-1)
        thisline+=",";
    }
    thisline+='}';
  }
  console.log("Posting: "+thisline);
  
  request.post(listener, {form:thisline}, function(err, response, body) {
    if(err!=null) {
      console.log(err);
   }
  });

  sentlines++;
  if(sentlines< nl) 
    setTimeout(loadFromFile, Math.floor(1000/appdef.frequency));
};

function load() {
  let obj= new Object();
  for(let i= 0; i< fields.length; i++) {
    if(fields[i]== "id") {
      let now= new Date().getTime();
      obj["id"]= now;
    }
    else {
       obj[fields[i]]= getRandomForType(types[i]);
    }
  }
  let loadstr= JSON.stringify(obj);
  console.log("Load: "+ loadstr);
  request.post(listener, {form:loadstr}, function(err, response, body) {
    if(err!=null) {
      console.log(err);
   }
});
  setTimeout(load, 1000);
  
}
module.exports = router;


