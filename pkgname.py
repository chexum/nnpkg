#!/usr/bin/python

import os
import re
import string

vendors={
	'libxml2':'xmlsoft',
	'libxml':'xmlsoft',
	'libxslt':'xmlsoft',

	'libgcrypt':'GNU',
	'libgpg-error':'GNU',
	'gzip':'GNU',
	'tar':'GNU',
	'cssc':'GNU',
	'diffutils':'GNU',
	'glpk':'GNU',
	'wdiff':'GNU',
	'global':'GNU',
        'groff':'GNU',
	'm4':'GNU',
	'libtool':'GNU',
	'automake':'GNU',
	'make':'GNU',
	'autoconf':'GNU',
	'libunistring':'GNU',
	'less':'GNU',
	'guile':'GNU',
	'grep':'GNU',
	'bison':'GNU',
	'gnutls':'GNU',

	'binutils':'Cygnus',

        'dhcp':'ISC',
        'bind':'ISC',
        'aftr':'ISC',

	'celt':'xiph.org',
	'libao':'xiph.org',
	'libogg':'xiph.org',
	'liboggz':'xiph.org',
	'libspiff':'xiph.org',
	'libxspf':'xiph.org',
	'speex':'xiph.org',
	'libfishsound':'xiph.org',

	'yaz':'indexdata',

	'pam_yubico':'yubico',
	'ykclient':'yubico',
	'libyubikey':'yubico',

	'linux-pam':'Linux',
	'pam':'Linux',
}

pkgnames={
	'openssh':'ssh',
	'linux-pam':'pam',
}

def pkgsplitname(fn):
	pkg=[]; pre=[]; ver=[]; post=[]; ext=[]
	SEP=['-','.','_',' ','+',',']
	TAGS='src all snapshot bin source orig open patch mingw32 release stable final alpha beta full package languages unixsrc wip linux'.split(' ')
	TYPE='src all snapshot current head git cvs svn trunk nightly'.split(' ')
	EXTO='asc sig sign pgp gpg md5 sha1 sha256 sha512 sha256sum part sha1sum md5sum checksum txt install exe msi'.split(' ')
	EXTI='zip z gz bz bz2 xz lzip lz lzma tar cpio tgz tz tbz tbz2 tlz jar war gem egg py patches tarp tp2'.split(' ')
	EXTI.extend('zoo arc arj lha lzh'.split(' '))
	w = re.split(r'([-_. +,])',fn)

	# special handling - either join or separate version from pkg name
	m = re.match(r'^(.*?)(\d+)$',w[0])
	# oggenc2.85srcs.zip
	if m and string.lower(m.group(1)) in [
			'iozone','leechr','dcron','gc',
			'oggenc','tcl','tk','xdelta','moconti','bash',
			'readline','ncurses',]:
		w[0]=m.group(1)
		w.insert(1,m.group(2))
	elif re.search(r'(?i)(gtk\+|c\+)',fn):
	# gtk sigc++
	# split without +
		w = re.split(r'([-_. ])',fn)

	if w[0] in ['jpegsrc','boost','libpng','dz','krb5','openssl','sysvinit','oggenc','qt','pam']:
		# jpegsrc.v8a.tar.gz
		if w[0] == 'jpegsrc':
			w[0] = 'src'
			w.insert(0,'jpeg')
		# libpng-1.2.43-apng.patch
		elif w[0] == 'libpng':
			TAGS.append('apng')
		elif w[0] == 'dz':
			TAGS.append('instrumentation')
		# krb5-1.4.3-signed.tar
		elif w[0] == 'krb5':
			TAGS.append('signed')
		elif w[0] == 'openssl':
			TAGS.append('srp')
		# sysvinit-2.88dsf
		elif w[0] == 'oggenc':
			w = re.split(r'(oggenc|srcs|[-_.])',fn)
			TAGS.append('srcs')
		elif w[0] == 'sysvinit':
			w = re.split(r'(dsf|[-_.])',fn)
			TAGS.append('dsf')
		elif w[0] == 'qt':
			TYPE.append('opensource')
			TYPE.append('everywhere')
			TYPE.append('x11')
			TYPE.append('free')
			TYPE.append('embedded')
		elif w[0] == 'pam':
			if re.match(r'^pam_.*',fn):
				w = re.split(r'([-.])',fn)
		else:
		# boost-jam
			w = re.split(r'(jam|[-_.])',fn)
		w=[i for i in w if i]
#	print "D",w
	pkg.append(w.pop(0))

	while len(w)>=2 and string.lower(w[-1]) in EXTO and w[-2] in SEP:
                ext.append(w.pop())
                ext.append(w.pop())

#	print pkg,pre,ver,post,ext,"!",w

	while len(w)>=2 and string.lower(w[-1]) in EXTI and w[-2] in SEP:
                ext.append(w.pop())
                ext.append(w.pop())
	ext.reverse()

	while len(w)>=1 and string.lower(w[-1]) in TAGS:
                post.append(w.pop())
		if len(w)>1 and w[-1] in SEP:
	                post.append(w.pop())
	post.reverse()

	# collect version fragments
	while len(w)>=1:
		m=re.match(r'(?i)^((\d*)([a-z]|diff|snap|git|stable|pl|pre|rel|rc|alpha|beta|gamma|patched|final|)(\d*?|\d+[a-z]|g[0-9a-f]{5,})|[0-9a-f]{16,})$',w[-1])
#		print pkg,"check",w[-1]
		if not m: break
#		print pkg,w,"is version",m.groups()
		ver.append(w.pop())
		if len(w)>1 and len(w[-1])==1:
			ver.append(w.pop())

	ver.reverse()
	if len(ver)>0 and ver[0] in SEP:
		w.append(ver.pop(0))

	# add anything not suspicious looking to the pkg name
	while len(w)>=2 and w[0] in SEP:
		if string.lower(w[1]) in TYPE:
			break
		if re.match('^\d+$',w[1]):
			# push version looking stuff to the version field
			w.extend(ver)
			ver=w[1:]
			w=[w[0]]
			break
		else:
			pkg.append(w.pop(0))
			pkg.append(w.pop(0))

	pre=w

	strver = ''.join(ver)
	if "." not in strver:
	  strver = strver.replace("-",".")
	  strver = strver.replace("_",".")

	strpkg = ''.join(pkg).lower()
	if strpkg in vendors:
	  strvnd = vendors[strpkg]
	else:
	  strvnd = ''

	if strpkg in pkgnames:
		pkgnam = pkgnames[strpkg]
        else:
		pkgnam = strpkg

	return {
		'pkg': strpkg,
		'pkgnam': pkgnam,
		'pre':''.join(pre),
		'ver':''.join(ver),
		'tag':''.join(post),
		'ext':''.join(ext),
		'vnd': strvnd,
		'dotver': strver,
		}

def processfile(f):
	(dir,fn)=os.path.split(f)
	dict=pkgsplitname(fn)
	dict['dir']=dir
	dict['fn']=fn
	return dict

def selftest():
	for test in (
		'abcl:-src-:0.20.0::.zip',
		'tcl::8.5.8:-src:.tar.gz',
		'libnetfilter_conntrack:-:0.0.101::.tar.bz2.sig',
		'w32api:-:3.14-3-msys-1.0.12:-src:.tar.lzma',
		'gpscorrelate:-:1.6.1::.tar.gz',
		'zenity:-:2.30.0::.sha256sum',
		'libevent:-:2.0.5:-beta:.tar.gz',
		'oggenc::2.85:srcs:.zip',
		'binstring:-:2.0.1_beta_2::.zip',
		'boost-jam::3.1.18::.tgz',
		'aria2:-:1.9.4::.tar.bz2',
		'asymptote:-:1.97:.src:.tgz.part',
		'atmailopen::::.tgz',
		'bind:-:9.6.1-P2::.tar.gz.sha512.asc',
		'cups:-:1.4.2:-source:.tar.bz2',
		'ethtool:-:2.6.33-pre1::.tar.gz',
		'GNUnet:-:0.8.1b::.tar.gz.sig',
		'cyrus-sasl:-:2.1.24rc1::.tar.gz',
		'dhcp:-:4.2.0b2::.tar.gz',
		'jpeg:src.:v8a::.tar.gz',
		'libpng:-:1.2.41:-apng.patch:',
		'gtk+:-:2.20.1::.sha256sum',
		'libconic:_:0.24+0m5::.tar.gz',
		'libsigc++:-:2.2.7::.tar.bz2',
		'openssl:-:1.0.0:+srp-patch:.txt',
		'link-grammar:-:4.6.7::.tar.gz',
		'moconti::102609::.tgz',
		'Leechr::0.4.8::.zip',
		'ucspi-tcp:-:0.88-ipv6.diff19::.bz2',
		'gc::7.0alpha7::.tar.gz',
		'divx611:-:20060201-gcc4.0.1::.tar.gz',
		'kamailio:-:1.5.2-tls:_src:.tar.gz',
		'ucspi-tcp:-:0.88-ipv6.diff17::.bz2.sig',
		'pam_p11:-:0.1.2::.tar.gz',
		'KDiff3Setup:_:0.9.88::.exe',	# is it worth to separate all setup for windows?
		'linuxha:,:1-0-8:,Linux:.tarp.gz',
		'linuxha12:+:1.2.2::.tp2',
		'engine_pkcs11:-:0.1.3::.tar.gz',
		'libp11:-:0.2.1::.tar.gz',
		'pam_p11:-:0.1.2::.tar.gz',
		'libp11:-:0.2.2::.tar.gz',
		'wv2:-:0.4.2::.tar.bz2',
		'wv:-:1.2.1::.tar.gz',
		'libX11:-:1.1.99.2::.tar.bz2',
		):
		fn=''.join(test.split(':'))
#		pkg pre ver tag ext
		res='%(pkg)s:%(pre)s:%(ver)s:%(tag)s:%(ext)s' % pkgsplitname(fn)
		if test != res:
			print "fail", fn, res
			print "want", fn, test

def main(argv=[]):
	if len(argv)==0:
		selftest()
		return

	format='%(pkg)s:%(pre)s:%(ver)s:%(tag)s:%(ext)s'
	# ugly positional argument check
	if re.search('%',argv[0]):
		format=argv.pop(0)

	for l in argv:
		print format % processfile(l)

if __name__ == '__main__':
        import sys

        sys.exit(main(sys.argv[1:]))
