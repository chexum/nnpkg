#!/usr/bin/python

import os
import string

NNPKGDIR='/var/lib/cxpkg'

# XXX fn -> match
def pkgmeta(fn):
	if os.path.isdir(NNPKGDIR):
		pass
	else:
		raise Exception,"no pkgdir"

	res={}
	try:
		with open(os.path.join(NNPKGDIR,'.'.join([fn,'desc']))) as f:
			for l in f:
				l=string.strip(l,' \r\n')
				kw=l.split(' ')
				tag=kw.pop(0)
				s=' '.join(kw)
				# descriptive pkg name including version and suite (kde/gnome, can be before name)
				if tag=='Name:':
					res['desc']=s
				# these will change
				elif tag=='Created:':
					res['created']=s
				elif tag=='Replaces:':
					res['replaces']=s
				elif tag=='Updated:':
					res['updated']=s
			res['pkgname']=fn
	except IOError:
		pass

	return res

def pkgcontents(pkg):
	raise Exception,"not implemented"

def main(argv=[]):
	for l in argv:
		print pkgmeta(l)

if __name__ == '__main__':
        import sys

        sys.exit(main(sys.argv[1:]))
