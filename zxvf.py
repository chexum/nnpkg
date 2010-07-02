#!/usr/bin/python

import os
import re
import string

SRCDIR='/usr/src'

def zxvf(fn):
	import pkgname
	prop = pkgname.pkgsplitname(fn)
	print "not unpacking", fn, prop
	return

def main(argv=[]):
	pwd = os.getcwd()
	if not re.search('^'+SRCDIR+'($|/)',pwd):
		raise ValueError
	
	for l in argv:
		zxvf(l)

if __name__ == '__main__':
        import sys

        sys.exit(main(sys.argv[1:]))
