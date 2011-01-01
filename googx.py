#!/usr/bin/python

import os
import re
import urlparse
import warnings

from twill.commands import go,load_cookies,save_cookies

def fetch(url):
	dom = ''
	o=urlparse.urlparse(url)
	print o.netloc
	cookiefile=os.path.expanduser('~/.cookie.'+dom)
	if os.path.exists(cookiefile):
		load_cookies(cookiefile)
	go('http://www.google.com/ncr')
	print "fetching", url
	save_cookies(cookiefile)

def main(argv=[]):
	warnings.filterwarnings( "ignore", category=DeprecationWarning, module="twill")
	for p in argv:
		if (re.match('https?://.*',p)):
			fetch(p)

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv[1:]))
