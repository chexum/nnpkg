#!/usr/bin/python

import sys
import os
import socket
import ssl
import re
from urlparse import urlparse

#import libproxy
#
#URL = "http://www.google.com"
#
#pf = libproxy.ProxyFactory()
#for proxy in pf.getProxies(URL):
#  # Do something with the proxy
#  if fetch_url(URL, proxy):
#    break

# *   - http://[username:password@]proxy:port
# *   - socks://[username:password@]proxy:port
# *   - socks5://[username:password@]proxy:port
# *   - socks4://[username:password@]proxy:port
# *   - <procotol>://[username:password@]proxy:port
# *   - direct://

default_ports={
    'http':80,
    'https':443,
    'ftp':21,
}

class MetaConnection:
    # self members:
    #     l7proto
    #     l3host
    #     l3port
    #     sslcafile

    def __init__(self,proto,host,port=None):
        """
          proto - http
          host -
          port 80,443 or nothing to deduce from proto
        """
        if port is None:
            if proto in default_ports:
                port = default_ports[proto]
            else:
                return None
        self.l7proto = proto
        self.l3host = host
        self.l3port = port
        self.sslcafile = None
        self.sock = None
        self.overssl = False
        self.oversocks = False
        self.unwritten = ''
        self.unread = ''
        self.eof = False
        self.debug = None

        if proto in ['https','ftps']:
            self.overssl = True
            self.ssl_init()

    def ssl_init(self,cadir=None,cafile=None):
        # XXX ugly
        # XXX perhost plus validity
        my_ca_certs = cafile if cafile else '/tmp/certs.txt'
        my_ca_dir = cadir if cadir else '/etc/ssl/certs'
        ca_count = 0
        if not os.path.exists(my_ca_certs):
            ca_f = open(my_ca_certs,'w')
            for fn in os.listdir(my_ca_dir):
                fullname = os.path.join(my_ca_dir,fn)
                try:
                    with open(fullname) as f:
                        q = f.read()
                        m = re.search('^(-{5}BEGIN CERTIFICATE-{5}$(.*\n)+^-{5}END CERTIFICATE-{5}$)',q,flags=re.MULTILINE)
                        if m:
                            print >>ca_f,m.group(1)
                            ca_count += 1
                except IOError:
                    return None
            ca_f.close()
        else:
            ca_count = 1

        if ca_count > 0:
            self.sslcafile = my_ca_certs
        else:
            os.remove(my_ca_certs)

    def _tcpconnect(self,host,port):
        sai = socket.getaddrinfo(host, port, 0, 0, socket.SOL_TCP)

        for (sfam, styp, sprot, snam, sa) in sai:
            s = socket.socket(sfam,styp,sprot)
            s.connect(sa)
            return s # XXX if success
        print 'no connect'

    def dossl(self):
        if self.sock and self.overssl:
            self.sslsock = ssl.wrap_socket(self.sock,cert_reqs=ssl.CERT_OPTIONAL,ca_certs=self.sslcafile)
            print self.sslsock.getpeercert()

    def connect(self):
        self.sock = self._tcpconnect(self.l3host, self.l3port)
        self.dossl()

    def connect_socks(self,sockshost,socksport=1080):
        s = self._tcpconnect(sockshost,socksport)
        if s is not None:
            # XXX if name
            # 0x04 0x01 PORTH PORTL 0 0 0 1 (user0) name0
            socksopen=r'%c%c%c%c%c%c%c%c%s%c%s%c'% (4,1,self.l3port/256,self.l3port&255,0,0,0,1,'',0,self.l3host,0,)
            s.send(socksopen)
            res=s.recv(8)
            if len(res) != 8 or res[1] != r'Z':
                pass
            else:
                self.sock = s
                self.oversocks = True
        self.dossl()

    def writeln(self,ln='',crlf='\r\n',flush=None,debug=None):
        self.unwritten = ''.join([self.unwritten,ln,crlf])

        if debug or self.debug or True:
            print '>',ln

        if len(self.unwritten)>16000 or ln == '' or flush:
            if self.overssl:
                self.sslsock.write(self.unwritten)
            else:
                self.sock.send(self.unwritten)
            self.unwritten=''

    def readln(self,stripcrlf=None,debug=None):
        start = self.unread.find('\n')
        while start < 0 and not self.eof:
            if self.overssl:
                newstr = self.sslsock.read()
            else:
                newstr = self.sock.recv(16000)
            if len(newstr) == 0:
                self.eof = True
            else:
                self.unread = self.unread + newstr
            start = self.unread.find('\n')

        if start >= 0:
            s = self.unread[:start+1]
            self.unread = self.unread[start+1:]
        else:
            s = self.unread
            self.unread=''

        if stripcrlf:
            s = s.rstrip('\r\n')

        if debug or self.debug:
            print '-',s.strip('\r\n')

        return s

    def httphdr(self,h,v=None,debug=None):
        hdrs={  'host':'',
                'user-agent':'',
                'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'accept-language':'en-us,en;q=0.5',
                'accept-encoding':'gzip,deflate',
                'accept-charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'keep-alive':'115',
                'connection':'keep-alive',
                }

        if not v:
            if h.lower() in hdrs:
                v = hdrs[h.lower()]
            else:
                v = ''

        self.writeln(''.join([h,': ',v]),debug=debug)

    def httpsend(self,uri,method='GET',httpver='1.1',debug=None):
        if self.l7proto not in ['http','https']:
            raise WhateverNeeded

        ua='Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 (.NET CLR 3.5.30729)'

        self.httpmethod = method
        self.httpver = httpver

        vertag = ''
        if httpver != '0.9':
            vertag = ' HTTP/%s'%(httpver,)

        # keep the order and contents as common as possible
        self.writeln('%s %s%s'%(method,uri,vertag,))
        # XXX :PORT
        self.httphdr('Host',self.l3host,debug)
        self.httphdr('User-Agent',ua)
        self.httphdr('Accept')
        self.httphdr('Accept-Language')
        self.httphdr('Accept-Encoding')
        self.httphdr('Accept-Charset')
        self.httphdr('Keep-Alive','115')
        self.httphdr('Connection','keep-alive')
#       self.httphdr('TE','trailers')
        self.writeln('',flush=True)

    def httpheaders(self,h):
        if h.lower() in self.httphdrs:
            return self.httphdrs[h.lower()]
        return ''

    def httpheadersa(self,h):
        return [z.strip(' ') for z in self.httpheaders(h).split(',')]

    def httpget(self,debug=None):
        if self.l7proto not in ['http','https']:
            raise WhateverNeeded

        self.httpstatus = self.readln(stripcrlf=True,debug=debug)
        self.httphdrs = {}

        while True:
            s = self.readln(stripcrlf=True,debug=debug)
            if s=='':
                break

            colon = s.find(':')
            if colon > 0:
                h = s[:colon].lower()
                v = s[colon+1:].strip(' ')
                if h == 'set-cookie':
                    arr = [z.strip(' ') for z in v.split(';')]
                    if len(arr)>0:
                        (n,v)=arr[0].split('=',1)
                        print 'cookie',n,arr
                    #XXX self.cookies
                else:
                    self.httphdrs[h]=v

        print 'moredata?',self.httpmethod != 'HEAD'
        if self.httpmethod == 'HEAD':
            return

        print 'cl:',self.httpheaders('content-length')
        print 'te:',self.httpheaders('transfer-encoding')
        print 'cc:',self.httpheadersa('cache-control')
        print 'v:',self.httpheadersa('vary')

def connect(proto,host,port=None,uri='/'):
    mc = MetaConnection(proto,host,port)
#   mc.connect()
    mc.connect_socks('192.168.88.254',9050)

    mc.httpsend(uri,debug=1)
    mc.httpget(debug=1)

# {'notAfter': 'Jun  8 23:59:59 2011 GMT',
#  'subjectAltName': (('DNS', 'panel.dreamhost.com'), ('DNS', 'www.panel.dreamhost.com')),
#  'subject': ((('organizationalUnitName', u'Domain Control Validated'),),
#              (('organizationalUnitName', u'Provided by New Dream Network, LLC'),),
#              (('organizationalUnitName', u'DreamHost Basic SSL'),),
#              (('commonName', u'panel.dreamhost.com'),))}

if __name__ == '__main__':
    for u in sys.argv[1:]:
        o = urlparse(u)
        connect(o.scheme,o.netloc,o.port,o.path)
