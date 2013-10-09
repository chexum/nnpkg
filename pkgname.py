#!/usr/bin/python
# vim: ts=2:sw=2:noet

import os
import re
import string

pkgnames={
	'openssh':'ssh',
	'linux-pam':'pam',
	'mesalib':'mesa',
	'mesaglut':'mesa',
	'pixman':'libpixman',
	'tiff':'libtiff',
	'libgsasl':'gsasl',
	'util-linux-ng':'util-linux',
	'gtk+':'gtk',
	'json-c':'json',
}

categories={
	'mesa':'X11',
	'xpyb':'X11',
	'libpciaccess':'X11',
}

vendors={
	'libxml2':'xmlsoft',
	'libxml':'xmlsoft',
	'libxslt':'xmlsoft',

	'gsasl':'GNU',
	'libgsasl':'GNU',
	'autoconf':'GNU',
	'automake':'GNU',
	'bash':'GNU',
	'bison':'GNU',
	'cpio':'GNU',
	'cssc':'GNU',
	'diffutils':'GNU',
	'ed':'GNU',
	'fileutils':'GNU',
	'findutils':'GNU',
	'gawk':'GNU',
	'gettext':'GNU',
	'global':'GNU',
	'glpk':'GNU',
	'gnutls':'GNU',
	'grep':'GNU',
	'groff':'GNU',
	'guile':'GNU',
	'gzip':'GNU',
	'less':'GNU',
	'libgcrypt':'GNU',
	'libgpg-error':'GNU',
	'libtool':'GNU',
	'libunistring':'GNU',
	'm4':'GNU',
	'make':'GNU',
	'nano':'GNU',
	'patch':'GNU',
	'pth':'GNU',
	'recode':'GNU',
	'screen':'GNU',
	'sh-utils':'GNU',
	'tar':'GNU',
	'texinfo':'GNU',
	'time':'GNU',
	'wdiff':'GNU',
	'which':'GNU',
	'acl':'SGI',
	'attr':'SGI',

	'binutils':'Cygnus',

	'dhcp':'ISC',
	'bind':'ISC',
	'aftr':'ISC',

	'celt':'xiph.org',
	'flac':'xiph.org',
	'libao':'xiph.org',
	'libfishsound':'xiph.org',
	'libogg':'xiph.org',
	'liboggz':'xiph.org',
	'libspiff':'xiph.org',
	'libtheora':'xiph.org',
	'libvorbis':'xiph.org',
	'libxspf':'xiph.org',
	'opus':'xiph.org',
	'speex':'xiph.org',
	'vorbis-tools':'xiph.org',

	'applewmproto':'X11',
	'bdftopcf':'X11',
	'bigreqsproto':'X11',
	'bitmap':'X11',
	'compiz':'X11',
	'compositeproto':'X11',
	'damageproto':'X11',
	'dmxproto':'X11',
	'dri2proto':'X11',
	'evieext':'X11',
	'fixesproto':'X11',
	'fontcacheproto':'X11',
	'fonts_100dpi':'X11',
	'fonts_75dpi':'X11',
	'fonts_cid':'X11',
	'fonts_core':'X11',
	'fontsproto':'X11',
	'font-util':'X11',
	'gccmakedep':'X11',
	'glproto':'X11',
	'iceauth':'X11',
	'imake':'X11',
	'inputproto':'X11',
	'kbproto':'X11',
	'libapplewm':'X11',
	'libdmx':'X11',
	'libdrm':'X11',
	'libfontenc':'X11',
	'libfs':'X11',
	'libice':'X11',
	'liblbxutil':'X11',
	'liboldx':'X11',
	'libpthread-stubs':'X11',
	'libsm':'X11',
	'libwindowswm':'X11',
	'libx11':'X11',
	'libxau':'X11',
	'libxaw':'X11',
	'libxcomposite':'X11',
	'libxcursor':'X11',
	'libxdamage':'X11',
	'libxdmcp':'X11',
	'libxevie':'X11',
	'libxext':'X11',
	'libxfixes':'X11',
	'libxfontcache':'X11',
	'libxfont':'X11',
	'libxft':'X11',
	'libxinerama':'X11',
	'libxi':'X11',
	'libxkbfile':'X11',
	'libxkbui':'X11',
	'libxmu':'X11',
	'libxpm':'X11',
	'libxprintapputil':'X11',
	'libxprintutil':'X11',
	'libxp':'X11',
	'libxrandr':'X11',
	'libxrender':'X11',
	'libxres':'X11',
	'libxscrnsaver':'X11',
	'libxtrap':'X11',
	'libxtst':'X11',
	'libxt':'X11',
	'libxvmc':'X11',
	'libxv':'X11',
	'libxxf86dga':'X11',
	'libxxf86misc':'X11',
	'libxxf86vm':'X11',
	'makedepend':'X11',
	'mkcfm':'X11',
	'mkcomposecache':'X11',
	'mkfontdir':'X11',
	'mkfontscale':'X11',
	'printproto':'X11',
	'randrproto':'X11',
	'recordproto':'X11',
	'rendercheck':'X11',
	'renderproto':'X11',
	'resourceproto':'X11',
	'scrnsaverproto':'X11',
	'setxkbmap':'X11',
	'trapproto':'X11',
	'util-macros':'X11',
	'videoproto':'X11',
	'windowswmproto':'X11',
	'xauth':'X11',
	'xbitmaps':'X11',
	'xcmiscproto':'X11',
	'xcursorgen':'X11',
	'xcursor-themes':'X11',
	'xdirs':'X11',
	'xdpyinfo':'X11',
	'xev':'X11',
	'xextproto':'X11',
	'xf86bigfontproto':'X11',
	'xf86dgaproto':'X11',
	'xf86driproto':'X11',
	'xf86-input-evdev':'X11',
	'xf86-input-keyboard':'X11',
	'xf86-input-mouse':'X11',
	'xf86miscproto':'X11',
	'xf86rushproto':'X11',
	'xf86-video-ati':'X11',
	'xf86-video-nouveau':'X11',
	'xf86-video-nv':'X11',
	'xf86vidmodeproto':'X11',
	'xfs':'X11',
	'xhost':'X11',
	'xineramaproto':'X11',
	'xinit':'X11',
	'xinput':'X11',
	'xkbcomp':'X11',
	'xkbdata':'X11',
	'xkbevd':'X11',
	'xkbprint':'X11',
	'xkbutils':'X11',
	'xlsfonts':'X11',
	'xmessage':'X11',
	'xmodmap':'X11',
	'xorg-cf-files':'X11',
	'xorg-server':'X11',
	'xorg-sgml-doctools':'X11',
	'xprop':'X11',
	'xproto':'X11',
	'xproxymanagementprotocol':'X11',
	'xrandr':'X11',
	'xrdb':'X11',
	'xsetmode':'X11',
	'xsetpointer':'X11',
	'xsetroot':'X11',
	'xset':'X11',
	'xtrans':'X11',
	'xvidtune':'X11',
	'xwd':'X11',
	'xwininfo':'X11',

	'libxcb':'X11',
	'xcb-proto':'X11',
	'xcb-util':'X11',
	'xcb-util-keysyms':'X11',
	'xcb-util-wm':'X11',
	'xcb-util-renderutil':'X11',
	'xcb-util-image':'X11',

	'yaz':'indexdata',

	'pam_yubico':'yubico',
	'ykclient':'yubico',
	'libyubikey':'yubico',

	'linux-pam':'Linux',
	'pam':'Linux',

	'gc':'Boehm',

	'ldns':'nlnetlabs',
	'nsd':'nlnetlabs',
	'unbound':'nlnetlabs',

	'httpd':'Apache',
	'apr':'Apache',
	'apr-util':'Apache',
}

def pkgsplitname(fn):
	pkg=[]; pre=[]; ver=[]; post=[]; ext=[]
	SEP=['-','.','_',' ','+',',']
	# tags that better stand separate from the version number (mostly better)
	TAGS='src all snapshot bin source orig open patch mingw32 release stable final alpha beta full'.split(' ')
	TAGS.extend('package languages unixsrc wip linux installer'.split(' '))
	TYPE='src all snapshot current head git cvs svn trunk nightly'.split(' ')
	# outside extensions, always at the end of the name
	EXTO='asc sig sign pgp gpg md5 sha1 sha256 sha512 sha256sum rsa dsa part sha1sum md5sum checksum txt install exe msi'.split(' ')
	EXTO.extend('zoo arc arj lha lzh rar'.split(' '))
	# real extensions that can occur more to the inside
	EXTI='zip z gz bz bz2 xz lzip lz lzma tar cpio tgz tz tbz tbz2 tlz jar war gem egg tarp tp2'.split(' ')
	EXTI.extend('patch patches diff diffs pdf html htm rom doc hex ps tex texi c py'.split(' '))
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
	elif re.search(r'([Gg]tk\+|[Cc]\+)',fn):
	# gtk sigc++ -resplit without +
		SEP=['-','.','_',' ',',']
		w = re.split(r'([-_. ])',fn)
	elif re.search(r'(?i)setup\d*$',w[0]):
		m = re.match(r'(?i)(.*?)(setup\d*)',w[0])
		w[0]=m.group(1)
		w[1]=''.join([m.group(2),w[1]])

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
#	print "D!",w
	pkg.append(w.pop(0))

	while len(w)>=2 and string.lower(w[-1]) in EXTO and w[-2] in SEP:
                ext.append(w.pop())
                ext.append(w.pop())

#	print "D!",pkg,pre,ver,post,ext,"!",w

	while len(w)>=2 and string.lower(w[-1]) in EXTI and w[-2] in SEP:
                ext.append(w.pop())
                ext.append(w.pop())
	ext.reverse()

	while len(w)>=1 and string.lower(w[-1]) in TAGS:
                post.append(w.pop())
		if len(w)>1 and w[-1] in SEP:
	                post.append(w.pop())
	post.reverse()

#	print "D!",pkg,pre,ver,post,ext,"!",w

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

	# coping with VVV(-X11R7.1-)VVV
	if re.match(r'^X11R\d+$',pkg[-1]) and pkg[-2] in ['-']:
		pre.insert(0,pkg[-1])
		pkg.pop(-1)
		pre.insert(0,pkg[-1])
		pkg.pop(-1)
		if re.match(r'\d+',ver[0]) and ver[1] in ['-']:
			pre.append(ver[0])
			ver.pop(0)
			pre.append(ver[0])
			ver.pop(0)
#	print "D!",pkg,pre,ver,post,ext

	strver = ''.join(ver)
	if "." not in strver:
	  strver = strver.replace("-",".")
	  strver = strver.replace("_",".")

	strpkg = ''.join(pkg)
	pkg_canonical = strpkg.lower()
	if pkg_canonical in vendors:
	  strvnd = vendors[pkg_canonical]
	else:
	  strvnd = ''

	if pkg_canonical in pkgnames:
		pkgnam = pkgnames[pkg_canonical]
	else:
		pkgnam = pkg_canonical

	pkgcat = ''
	if pkgnam in categories:
		pkgcat = categories[pkgnam]

	if pkgnam in ['sqlite-src','sqlite-amalgamation','sqlite-autoconf']:
		m=re.match(r'^(sqlite)(-.*)',pkgnam)
		strpkg=m.group(1)
		pre=m.group(2)+'-'
		m=re.match(r'^([3-9])(\d\d)(\d\d)(\d\d)',ver[0])
		if m:
			strver="%d.%d" % (int(m.group(1))+0,int(m.group(2))+0,)
			if int(m.group(3)):
				strver = strver + '.' + "%d" % (int(m.group(3))+0,)
			if int(m.group(4)):
				strver = strver + '.' + "%d" % (int(m.group(4))+0,)
			pkg_canonical='sqlite'
			pkgnam='sqlite3'

	if pkgnam=='lvm2':
		pkgnam='lvm'

	if pkgnam=='libusbx':
		pkgnam='libusb'

	if pkgnam in ['libusb','libusb-compat'] and ver[0]=='0':
		pkgnam='libusb_compat'

	if strvnd == 'X11':
		pkgcat = 'X11'
		pkgnam = 'X11_' + strpkg

	return {
		'pkg': strpkg,
		'pre':''.join(pre),
		'ver':''.join(ver),
		'tag':''.join(post),
		'ext':''.join(ext),
		'vnd': strvnd,
		'dotver': strver,
		'pkgnam': pkgnam,
		'pkgcat': pkgcat,
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
		'GNUnet:-:0.8.1b::.tar.gz.sig/gnunet',
		'cyrus-sasl:-:2.1.24rc1::.tar.gz',
		'dhcp:-:4.2.0b2::.tar.gz',
		'jpeg:src.:v8a::.tar.gz',
		'libpng:-:1.2.41:-apng:.patch',
		'gtk+:-:2.20.1::.sha256sum/gtk',
		'libconic:_:0.24+0m5::.tar.gz',
		'libsigc++:-:2.2.7::.tar.bz2',
		'openssl:-:1.0.0:+srp:-patch.txt',
		'link-grammar:-:4.6.7::.tar.gz',
		'moconti::102609::.tgz',
		'Leechr::0.4.8::.zip',
		'ucspi-tcp:-:0.88-ipv6.diff19::.bz2',
		'gc::7.0alpha7::.tar.gz',
		'divx611:-:20060201-gcc4.0.1::.tar.gz',
		'kamailio:-:1.5.2-tls:_src:.tar.gz',
		'ucspi-tcp:-:0.88-ipv6.diff17::.bz2.sig',
		'pam_p11:-:0.1.2::.tar.gz',
		'KDiff3:Setup_:0.9.88::.exe/kdiff3',	# is it worth to separate all setup for windows?
		'linuxha:,:1-0-8:,Linux:.tarp.gz',
		'linuxha12:+:1.2.2::.tp2',
		'engine_pkcs11:-:0.1.3::.tar.gz',
		'libp11:-:0.2.1::.tar.gz',
		'pam_p11:-:0.1.2::.tar.gz',
		'libp11:-:0.2.2::.tar.gz',
		'wv2:-:0.4.2::.tar.bz2',
		'wv:-:1.2.1::.tar.gz',
		'libX11:-:1.1.99.2::.tar.bz2',
		'openssh:-:5.9p1::.tar.gz/ssh',
		'Linux-PAM:-:1.1.5::.tar.bz2/pam',
		'putty:-:0.61::.tar.gz',
		'putty:-:0.61:-installer:.exe.DSA',
		'xorg-server:-:1.9.5::.tar.bz2/X11_xorg-server',
		'liblbxutil:-X11R7.1-:1.0.1::.tar.gz',
		'cryptsetup:-:1.1.3::.tar.bz2',
		'TrueCrypt: Setup :6.3::.exe.sig',
		'LVM2:.:2.02.64::.tgz',
		'sqlite:-autoconf-:3070603::.tar.gz/sqlite3',
		'gtk+:-:2.24.8::.tar.xz/gtk',
		'json-c:-:0.9::.tar.gz/json',
		'libusb-compat:-:0.1.5::.tar.bz2/libusb_compat',
		'libusbx:-:1.0.17::.tar.bz2/libusb',
		):
		exp=''.join(test.split(':'))
		w=exp.split('/')
		fn=w[0]
		if len(w)>1:
			res='%(pkg)s:%(pre)s:%(ver)s:%(tag)s:%(ext)s/%(pkgnam)s' % pkgsplitname(w[0])
		else:
			res='%(pkg)s:%(pre)s:%(ver)s:%(tag)s:%(ext)s' % pkgsplitname(w[0])
#		pkg pre ver tag ext
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
