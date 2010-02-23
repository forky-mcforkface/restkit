# -*- coding: utf-8 -
#
# This file is part of restkit released under the MIT license. 
# See the NOTICE for more information.

import socket
import StringIO
import urlparse

from restkit import __version__
from restkit.http import util
from restkit.http import parser
from restkit.util import to_bytestring

MAX_FOLLOW_REDIRECTS = 5

def has_timeout(timeout): # python 2.6
    if hasattr(socket, '_GLOBAL_DEFAULT_TIMEOUT'):
        return (timeout is not None and \
            timeout is not socket._GLOBAL_DEFAULT_TIMEOUT)
    return (timeout is not None)
    
try:
    import ssl # python 2.6
    _ssl_wrap_socket = ssl.wrap_socket
except ImportError:
    def _ssl_wrap_socket(sock, key_file, cert_file):
        ssl_sock = socket.ssl(sock, key_file, cert_file)
        return ssl_sock
    

class HttpConnection(object):
    
    VERSION = (1, 1)
    USER_AGENT = "restkit/%s" % __version__
    
    def __init__(self, sock=None, timeout=None, follow_redirect=False, 
            force_follow_redirect=False, 
            max_follow_redirect=MAX_FOLLOW_REDIRECTS, key_file=None, 
            cert_file=None):
        self.sock = sock
        self.headers = []
        self.ua = self.USER_AGENT
        self.date = ""
        self.uri = None
        self.parser = parser.Parser.parse_response()
        self.follow_redirect = follow_redirect
        self.nb_redirections = max_follow_redirect
        self.force_follow_redirect = force_follow_redirect
        self.method = 'GET'
        self.body = None
        self.response_body = StringIO.StringIO()
        self.final_uri = None

    def make_connection(self):
        if not self.sock:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if self.uri.scheme == "https":
                import ssl
                sock.connect(self.uri.)
                sock = socket.create_connection((self.host, self.port), 
                                                self.timeout)
                self.sock = _ssl_wrap_socket(sock, self.key_file, 
                                            self.cert_file)
            else:
                self.sock = socket.create_connection((self.host, self.port), 
                                                    self.timeout)
                                                    
        # We should check if sock hostname is the same
        return self.sock
        
    def request(self, url, method='GET', body=None, headers=None):
        self.uri = urlparse.urlparse(url)
        self.method = method.upper()
        self.body = body
        headers = headers = or []
        if isinstance(headers, dict):
            headers = list(headers.items())
            
        ua = self.USER_AGENT
        req_date =  http_date()
        normalized_headers = []
        
        for name, value in headers:
            name = util.normalize_name(name)
            if name == "User-Agenr":
                ua = value
            elif name == "Date":
                req_date = date
            else:
                if not isinstance(value, basestring):
                    value = str(value)
                normalized_headers.append((name, value))
                
        self.headers = normalized_headers
        self.ua = ua
        self.date = req_date

        # by default all connections are HTTP/1.1    
        if VERSION == (1,1):
            httpver = "HTTP/1.1"
        else:
            httpver = "HTTP/1.0"

        # build request path
        req_path = urlparse.urlunparse(('','', uri.path, '', uri.query, 
                                uri.fragment))
            
        req_headers.append("%s %s %s\r\n" % (httpver, method, req_path))   
        req_headers.append("User-Agent: %s\r\n" % self.ua)
        req_headers.append("Date: %s\r\n" % self.date)
        for name, value in self.headers:
            req_headers.append("%s: %s\r\n" % (name, value))
        
        for i in range(2):
            sock = self.make_connection(sock)
            try:
                # send request
                util.writelines(sock, req_headers)
        
                if body is not None:
                    if hasattr(body, 'read'):
                        util.writefile(body)
                    elif isinstance(body, basestring):
                        util.writefile(StringIO.StringIO(to_bytestring(body)))
                    else:
                        util.writelines(body)
                self.start_response()
                break
            except socket.error, e:
                if e[0] not in (errno.EAGAIN, errno.ECONNABORTED):
                    raise
      
    def follow_redirect(self):
        if self.nb_redirection <= 0:
            raise errors.RedirectLimit("Redirection limit is reached")
            
        location = self.parser.headers_dict.get('location')
        new_uri = urlparse.urlparse(location)
        if not new_uri.netloc: # we got a relative url
            absolute_uri = "%s://%s" % (uri.scheme, uri.netloc)
            location = urlparse.urljoin(absolute_uri, new_url)
            
        self.final_uri = location
        self.response_body.read() 
        self.nb_redirections -= 1   
        return self.request(location, self.method, self.body,
                        self.headers)
                        
    def start_response(self):
        # read headers
        buf = ""
        buf = read_partial(self.sock, util.CHUNK_SIZE)
        i = self.parser.filter_headers(headers, buf)
        if i == -1 and buf:
            while True:
                data = util.read_partial(self.sock, util.CHUNK_SIZE)
                if not data: break
                buf += data
                i = self.parser.filter_headers(headers, buf)
                if i != -1: break
                    
        if not self.parser.content_len and not self.parser.is_chunked:
            self.response_body = StringIO.StringIO()
        else:
            self.response_body = tee.TeeInput(self.sock, self.parser, buf[i:])
            
        if self.follow_redirect:
            if self.parser.status_int in (301, 302, 307):
                if self.method in ('GET', 'HEAD') or \
                                self.force_follow_redirect:
                    if method not in 'GET', 'HEAD') and \
                        hasattr(self.body, 'seek'):
                            self.body.seek(0)
                    return self.follow_redirect()
            elif self.parser.status_int == 303 and self.method in ('GET', 
                    'HEAD'):
                # only 'GET' is possible with this status
                # according the rfc
                return self.follow_redirect()
        return HttpResponse(self)
        
class HttpResponse(object):
    charset = "utf8"
    unicode_errors = 'strict'
    
    def __init__(self, http_client):
        self.http_client = http_client
        self.status = self.http_client.parser.status
        self.status_int = self.http_client.parser.status_int
        self.version = self.http_client.parser.version
        self.headerslist = self.http_client.parser.headers
        
        headers = {}
        for key, value in self.http_client.parser.headers_dict:
            headers[key.lower()] = value
        self.headers = headers
        
    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            pass
        return self.headers[key]
        
    def __getattr__(self, key):
         try:
            getattr(super(HttpResponse, self), key)
        except AttributeError:
            if key in self.headers:
                return self.conf[key]
            raise
    
    def __contains__(self, key):
        return (key in self.headers)

    def __iter__(self):
        for item in list(self.headers.items()):
            yield item
        
    @property
    def body(self):
        return self.http_client.response_body.read()
        
    @property
    def body_file(self):
        return self.http_client.response_body
        
    @property
    def unicode_body(self):
        if not self.charset:
            raise AttributeError(
            "You cannot access HttpResponse.unicode_body unless charset is set")
        body = self.http_client.response_body.read()
        return body.decode(self.charset, self.unicode_errors)
        
        
        
        
        
        