#!/usr/bin/python

from __future__ import print_function
import sys
import re
import os
from glob import glob
from subprocess import Popen,PIPE
import stat

VARPKG='/var/lib/cxpkg'

#  644     root     root      704 F ./usr/lib/libfftw.la
#  755     root     root   167318 F ./usr/lib/libfftw.so.2.0.7
LNRE=re.compile(r'\s+(?P<mode>[0-7]+)\s+(?P<user>.*?)\s+(?P<group>.*?)\s+(?P<size>.*?)\s+(?P<type>.*?)\s+(?P<name>.*?)(\s(?P<link>.*))')
NULL=open("/dev/null")

def checkexe(fn):
	bydict=dict()
	needsdict=dict()
	fordict=dict()
	data=[]

	try:
		with open(fn) as f:
			if f.read(4) != "\x7fELF":
				return data
			with Popen(['readelf','-d','-p','.comment','-V','--',fn],stdin=NULL,stdout=PIPE,stderr=NULL).stdout as p:
				for l in p:
# 0x00000001 (NEEDED)                     Shared library: [ld-linux.so.2]
					z=re.match(r'.*\(NEEDED\).*Shared.*\[(.*)\]',l)
					if z:
						needsdict[z.group(1)]=None
# 0x0000000e (SONAME)                     Library soname: [libopcodes-2.20.1.20100303.so]
					z=re.match(r'.*\(SONAME\).*soname.*\[(.*)\]',l)
					if z:
						data.append("%s %s %s" % (fn,"provides",z.group(1)))
#String dump of section '.comment':
#  [     0]  GCC: (GNU) 4.5.0
					z=re.match(r'.*GCC.*?\(GNU\)?\s+(.*)',l)
					if z:
						bydict[z.group(1)]=None
					z=re.match(r'.*Name:\s+(.*?)\s+Flags:.*',l)
					if z:
						fordict[z.group(1)]=None
#-V
#Version needs section '.gnu.version_r' contains 2 entries:
# Addr: 0x00000000080489bc  Offset: 0x0009bc  Link: 5 (.dynstr)
#  000000: Version: 1  File: libpopt.so.0  Cnt: 1
#  0x0010:   Name: LIBPOPT_0  Flags: none  Version: 3
#  0x0020: Version: 1  File: libc.so.6  Cnt: 1
#  0x0030:   Name: GLIBC_2.0  Flags: none  Version: 2

	except IOError:
		data.append("%s %s" % (fn,"unreadable"))

	l = needsdict.keys(); l.sort()
	for k in l:
		data.append("%s %s %s" % (fn,"needs",k))
	l = bydict.keys(); l.sort()
	for k in l:
		data.append("%s %s %s" % (fn,"by",k))
	l = fordict.keys(); l.sort()
	for k in l:
		data.append("%s %s %s" % (fn,"for",k))

	return data

def checkpkg(pkg):
	if not re.match(r'(.*\.xf)',pkg): pkg=os.path.join(VARPKG,pkg+'.xf')

	m=re.match(r'.*/(.*?)\.xf$',pkg)
	if m:
		pkgname=m.group(1)
		cachebase=os.path.join('.cache',pkgname)
	else:
		pkgname=None
		cachebase=None

	if cachebase is not None:
		try:
			if os.path.exists(cachebase+'.qf'):
				cacheinfo=os.stat(cachebase+'.qf')
			else:
				cacheinfo=None
			pkginfo=os.stat(pkg)
			if cacheinfo and cacheinfo[stat.ST_MTIME] >= pkginfo[stat.ST_MTIME]:
				with open(cachebase+'.qf') as f:
					for l in f:
						print(l,end='')
				return
		except EnvironmentError:
			pass

		try:
			if not os.path.exists('.cache'):
				os.mkdir('.cache')
			cachefile=open(cachebase+'.qq','w')
		except EnvironmentError:
			cachebase = None
			cachefile = sys.stdout

	try:
		with open(pkg) as f:
			for l in f:
				m = LNRE.match(l)
				if m:
					(mode,size,type,name,link)=m.group('mode','size','type','name','link')
					if type == 'F' and re.match(r'.*[75]\d\d',mode):
						for l in checkexe(name[1:]):
							print(l,file=cachefile)
	except IOError:
		print(pkg, "cannot be opened")
	
	if cachebase is not None:
		cachefile.close()
		os.rename(cachebase+'.qq',cachebase+'.qf')
		with open(cachebase+'.qf') as f:
			for l in f:
				print (l,end='')

	
def main(argv=None):
	if argv is None: argv = sys.argv[1:]
	if argv == []:
		# sorted - but with C locale
		for f in glob(os.path.join(VARPKG,"*.xf")): checkpkg(f)
	else:
		for p in argv: checkpkg(p)

if __name__ == '__main__':
	try:
		sys.exit(main())
	except KeyboardInterrupt:
		pass
	
	sys.exit(1)
