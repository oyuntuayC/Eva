var express = require('express');
var app = require('express')();
var http = require('http');

const {createProxyMiddleware} = require('http-proxy-middleware');
const httpServer = http.createServer(app).listen(80);

app.use('/webhooks/rest/webhook', createProxyMiddleware({target:'http://127.0.0.1:5005'}));
//app.use('/search', createProxyMiddleware({target:'http://www.google.com'}));
app.use(express.static('public',{index:'index.html'}));

