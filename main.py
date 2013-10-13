#!/usr/bin/env python
import sys, os
import re

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

#meta:
#PKG=sqlite
#PKGNAM=sqlite3
#PKGVER=3.8.2
#PKGVND=
#PKGCAT=

# args: zxvf/extract setup build install walk/package
# TODO: cross
# /x/i386/native
# /x/i686/mipsel/usr/include

DEBUG=False
build_dir.set_debug(DEBUG)
build_dir.setup()
build_dir.build()
build_dir.install()

if os.path.isdir('ROOT'):
  build_dir.command(["cxfilelist"])

with open('.cxpkg') as f:
  print
  for l in f:
    if not re.search("^[A-Z]+=",l):
      print l,
