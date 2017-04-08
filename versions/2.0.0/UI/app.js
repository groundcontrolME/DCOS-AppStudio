var express = require('express');
var path = require('path');
var favicon = require('serve-favicon');
var logger = require('morgan');
var cookieParser = require('cookie-parser');
var bodyParser = require('body-parser');

var index = require('./routes/index');
var menu = require('./routes/menu');
var httpProxy = require('http-proxy');
var proxy = httpProxy.createProxyServer({});

var app = express();
var session = require('express-session');
app.set('trust proxy', 1) // trust first proxy 
app.use(session({
  secret: 'keyboard cat',
  resave: false,
  saveUninitialized: true,
  cookie: { secure: true }
}))

// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

// uncomment after placing your favicon in /public
//app.use(favicon(path.join(__dirname, 'public', 'favicon.ico')));
app.use(logger('dev'));
app.use(function(req, res, next) {
  var sess = req.session;
  let inkibana= false;
  if(sess.inkibana!= null)
    inkibana= sess.inkibana;

  let uri= req.url;
  if(inkibana || uri.includes("elastic") || uri.includes("login") || uri.includes("kibana") || uri.includes("bundle") || uri.includes("api") || uri.includes("status")) {
   
   if(uri.includes("logout")|| uri.includes("menu") || uri=== "/") {
     inkibana= false;
     res.writeHead(301,
      {Location: '/menu'}
    );
    res.end();
     return;
   }
   if(uri.includes("login")) {
     inkibana= true;
   }
   sess.inkibana= inkibana;
    console.log("Proxy Kibana: "+req.url);
  //1.8.8  proxy.web(req, res, { target: 'http://kibana.marathon.l4lb.thisdcos.directory:5601' });
  if(uri.includes("/service/elastic/kibana/")) {
    req.url= uri.substring("/service/elastic/kibana/".length);
    console.log("Effective Proxy Kibana: "+req.url);  
  }
  
  proxy.web(req, res, { target: 'http://elastic:changeme@kibana.elastic.l4lb.thisdcos.directory:5601' });
}
 else {
    next();
  }
});


app.use(bodyParser.text({type: '*/*'}));
app.use(bodyParser.raw());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

app.use('/', index);

app.use('/menu', menu);

// catch 404 and forward to error handler
app.use(function(req, res, next) {
  var err = new Error('Not Found');
  err.status = 404;
  next(err);
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
  res.status(err.status || 500);
  res.render('error');
});

module.exports = app;
