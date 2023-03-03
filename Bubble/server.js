var express = require('express');
var app = require('express')();
var http = require('http');


const httpServer = http.createServer(app).listen(80);


app.use(express.static('public'));
