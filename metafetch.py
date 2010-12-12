#!/usr/bin/python

import sys
import os
import socket
import ssl
import re
from urlparse import urlparse

default_ports={
    'http':80,
    'https':443,
    'ftp':21,
}

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

def connect(proto,host,port=None):
    """
      proto - http
      host -
      port 80,443 or nothing to deduce from proto
    """

    if port is None:
        if proto in default_ports:
            port = default_ports[proto]
        else:
            raise Error

    my_ca_certs = '/tmp/certs.txt'
    my_ca_dir = '/etc/ssl/certs'
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
            except IOError as e:
                print e
                pass
        ca_f.close()

    # steps:
    # if socks:
    #   open conn to socks
    #   establish sock
    # else:
    #   establish tcp
    # if ssl:
    #   wrap ssl
    #
    over_socks = 0
    over_ssl = 0
    SOCKS_SERVER='192.168.88.254'
    SOCKS_PORT=9050
    if SOCKS_SERVER:
        over_socks = 1
        sai = socket.getaddrinfo(SOCKS_SERVER,SOCKS_PORT,0,0,socket.SOL_TCP)
    else:
        sai = socket.getaddrinfo(host, port, 0, 0, socket.SOL_TCP)

    for (sfam, styp, sprot, snam, sa) in sai:
        s = socket.socket(sfam,styp,sprot)
        s.connect(sa)
        # XXX if name
        # 0x04 0x01 PORTH PORTL 0 0 0 1 (user0) name0
        if over_socks:
            socksopen=r'%c%c%c%c%c%c%c%c%s%c%s%c'% (4,1,port/256,port&255,0,0,0,1,'',0,host,0,)
            s.send(socksopen)
            res=s.recv(8)
            print 'q',res,'q'
        if proto in ('https','ftps'):
            over_ssl = 1
            s = ssl.wrap_socket(s,cert_reqs=ssl.CERT_OPTIONAL,ca_certs=my_ca_certs)
            print s.getpeercert()
# {'notAfter': 'Jun  8 23:59:59 2011 GMT',
#  'subjectAltName': (('DNS', 'panel.dreamhost.com'), ('DNS', 'www.panel.dreamhost.com')),
#  'subject': ((('organizationalUnitName', u'Domain Control Validated'),),
#              (('organizationalUnitName', u'Provided by New Dream Network, LLC'),),
#              (('organizationalUnitName', u'DreamHost Basic SSL'),),
#              (('commonName', u'panel.dreamhost.com'),))}
        break

    if over_ssl:
        s.write('GET / HTTP/1.0\r\n')
        s.write('Host: %s\r\n'%(host,))
        s.write('\r\n')
    else:
        s.send('GET / HTTP/1.0\r\n')
        s.send('Host: %s\r\n'%(host,))
        s.send('\r\n')
    while 1:
        if over_ssl:
            l=s.read()
        else:
            l=s.recv(4096)
        if not l:
            break
        print l,

if __name__ == '__main__':
    for u in sys.argv[1:]:
        o = urlparse(u)
        connect(o.scheme,o.netloc,o.port)
