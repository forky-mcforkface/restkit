# -*- coding: utf-8 -
#
# This file is part of restkit released under the MIT license. 
# See the NOTICE for more information.

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
import os
import socket
import threading
import unittest
import urlparse
import urllib2

from restkit import httpc
from restkit.rest import Resource, RestClient
from restkit.errors import RequestFailed, ResourceNotFound, \
Unauthorized, RequestError


import t

from _server_test import HOST, PORT, run_server_test
run_server_test()


def 001_test():
    res = Resource("http://localhost")
    t.eq(res._make_uri("http://localhost", "/"), "http://localhost/")
    t.eq(res._make_uri("http://localhost/"), "http://localhost/")
    t.eq(res._make_uri("http://localhost/", "/test/echo"), 
        "http://localhost/test/echo")
    t.eq(res._make_uri("http://localhost/", "/test/echo/"), 
        "http://localhost/test/echo/")
    t.eq(res._make_uri("http://localhost", "/test/echo/"),
        "http://localhost/test/echo/")
    t.eq(res._make_uri("http://localhost", "test/echo"), 
        "http://localhost/test/echo")
    t.eq(res._make_uri("http://localhost", "test/echo/"),
        "http://localhost/test/echo/")

class ResourceTestCase(unittest.TestCase):

    def setUp(self):
        self.url = 'http://%s:%s' % (HOST, PORT)
        self.res = Resource(self.url)

    def tearDown(self):
        self.res = None

    def testGet(self):
        result = self.res.get()
        self.assert_(result.body == "welcome")
        self.assert_(result.status_int== 200)

    def testUnicode(self):
        result = self.res.get('/unicode')
        self.assert_(result.body == "éàù@")

    def testUrlWithAccents(self):
        result = self.res.get('/éàù')
        self.assert_(result.body == "ok")
        self.assert_(result.status_int == 200)

    def testUrlUnicode(self):
        result = self.res.get(u'/test')
        self.assert_(result.body == "ok")
        self.assert_(result.status_int == 200)
        result = self.res.get(u'/éàù')
        self.assert_(result.body == "ok")
        self.assert_(result.status_int == 200)

    def testGetWithContentType(self):
        result = self.res.get('/json', 
            headers={'Content-Type': 'application/json'})
        self.assert_(result.status_int == 200)
        def bad_get():
            result = self.res.get('/json', 
                headers={'Content-Type': 'text/plain'})
        self.assertRaises(RequestFailed, bad_get) 

    def testGetWithContentType2(self):
        res = Resource(self.url,
            headers={'Content-Type': 'application/json'})
        result = res.get('/json')
        self.assert_(result.status_int == 200)
        

    def testNotFound(self):
        def bad_get():
            result = self.res.get("/unknown")

        self.assertRaises(ResourceNotFound, bad_get)

    def testGetWithQuery(self):
        result = self.res.get('/query', test="testing")
        self.assert_(result.status_int == 200)

    def testGetWithIntParam(self):
        result = self.res.get('/qint', test=1)
        self.assert_(result.status_int == 200)

    def testSimplePost(self):
        result = self.res.post(payload="test")
        self.assert_(result.body=="test")

    def testPostByteString(self):
        result = self.res.post('/bytestring', payload="éàù@")
        self.assert_(result.body == "éàù@")

    def testPostUnicode(self):
        result = self.res.post('/unicode', payload=u"éàù@")
        self.assert_(result.body == "éàù@")

    def testPostWithContentType(self):
        result = self.res.post('/json', payload="test",
                headers={'Content-Type': 'application/json'})
        self.assert_(result.status_int == 200 )
        def bad_post():
            result = self.res.post('/json', payload="test",
                    headers={'Content-Type': 'text/plain'})
        self.assertRaises(RequestFailed, bad_post)

    def testEmptyPost(self):
        result = self.res.post('/empty', payload="",
                headers={'Content-Type': 'application/json'})
        self.assert_(result.status_int == 200 )
        result = self.res.post('/empty',headers={'Content-Type': 'application/json'})
        self.assert_(result.status_int == 200 )

    def testPostWithQuery(self):
        result = self.res.post('/query', test="testing")
        self.assert_(result.status_int == 200)
    
    def testPostForm(self):
        result = self.res.post('/form', payload={ "a": "a", "b": "b" })
        self.assert_(result.status_int == 200)

    def testSimplePut(self):
        result = self.res.put(payload="test")
        self.assert_(result.body=="test")

    def testPutWithContentType(self):
        result = self.res.put('/json', payload="test",
                headers={'Content-Type': 'application/json'})
        self.assert_(result.status_int== 200 )
        def bad_put():
            result = self.res.put('/json', payload="test",
                    headers={'Content-Type': 'text/plain'})
        self.assertRaises(RequestFailed, bad_put)

    def testEmptyPut(self):
        result = self.res.put('/empty', payload="",
                headers={'Content-Type': 'application/json'})
        self.assert_(result.status_int == 200 )
        result = self.res.put('/empty',headers={'Content-Type': 'application/json'})
        self.assert_(result.status_int == 200 )

    def testPutWithQuery(self):
        result = self.res.put('/query', test="testing")
        self.assert_(result.status_int== 200)

    def testHead(self):
        result = self.res.head('/ok')
        self.assert_(result.status_int == 200)

    def testDelete(self):
        result = self.res.delete('/delete')
        self.assert_(result.status_int == 200)

    def testFileSend(self):
        content_length = len("test")
        import StringIO
        content = StringIO.StringIO("test")
        result = self.res.post('/json', payload=content,
                headers={
                    'Content-Type': 'application/json',
                    'Content-Length': str(content_length)
                })

        self.assert_(result.status_int == 200 )

    def testFileSend2(self):
        import StringIO
        content = StringIO.StringIO("test")

        def bad_post():
            result = self.res.post('/json', payload=content,
                headers={'Content-Type': 'application/json'})

        self.assertRaises(RequestError, bad_post)

    def testBasicAuth(self):
        transport = httpc.HttpClient()
        transport.add_authorization(httpc.BasicAuth("test", "test"))

        res = Resource(self.url, transport)
        result = res.get('/auth')
        self.assert_(result.status_int == 200)

        transport = httpc.HttpClient()
        def niettest():
            res = Resource(self.url, transport)
            result = res.get('/auth')
        self.assertRaises(Unauthorized, niettest)
        