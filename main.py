#!/usr/bin/env python
import sys, os

argv = sys.argv
exe = os.path.realpath(argv[0])
exepath = os.path.split(exe)[0] or '.'
#exeprefix = os.path.split(os.path.abspath(exepath))[0]

cmdpath = os.path.join(exepath, 'cmd')
libpath = os.path.join(exepath, 'lib')

sys.path[:0] = [libpath]
os.environ['PYTHONPATH'] = libpath + ':' + os.environ.get('PYTHONPATH', '')

from nnpkg import build
build_dir = build.BuildDir(os.environ.get('NNPKG_ROOT',None))
print "IN",build_dir.get_root()
build_dir.set_debug(True)

#meta:
#PKG=sqlite
#PKGNAM=sqlite3
#PKGVER=3.8.2
#PKGVND=
#PKGCAT=

#nnpkg_root=/usr/src/sqlite-autoconf-3080002/.nnpkg
#nnpkg log config -> |tee /dev/stderr|multilog t s1000000 n10 $NNPKG/config
#nnpkg configure |
#export CC CXX ADAC
#export CFLAGS CXXFLAGS LDFLAGS

DEBUG=True
build_dir.setup()
build_dir.build()
build_dir.install()

#if not os.path.isdir("ROOT"):
#build_dir.command(["cxroot","$ROOT","make","INSTALL=install","DESTROOT=$ROOT","install"],
#["ROOT=%s/ROOT"%(build_dir.get_root(),)])
# python setup.py install --root "`pwd`/ROOT"
#else:
#raise 'Already ROOT'
#
if os.path.isdir('ROOT'):
  build_dir.command(["cxfilelist"])

sys.exit(1)


