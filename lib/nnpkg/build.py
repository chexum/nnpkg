import os
import subprocess
import re

def multigrep(fn,pairs):
  found={}
  re_compiled = re.compile("|".join([search for opt,search,err in pairs]))

  with open(fn) as f:
    for l in f:
      res = re_compiled.search(l)
      if res:
        for opt,search,err in pairs:
          if re.search(search,l):
            found[opt]=l

  return [opt for opt,search,err in pairs if opt in found]

class Package:
  def __init__(self,type,script,dir="."):
    self.conf_script=script
    self.conf_dir=dir
    self.conf_type=type
    self.conf_file=None

  def setup(self,builddir):
    raise "Can't configure an unknown package!"

  def build(self,builddir):
    builddir.command(["make",])

  def install(self,builddir):
#ROOT=/usr/src/tig-1.2/ROOT
#cxroot $ROOT make INSTALL=install DESTDIR=$ROOT install
    builddir.command(["make","DESTDIR=$ROOT","install","install-doc-man"],["ROOT=%s"%(builddir.get_destdir())])

class AutoconfPackage(Package):
  def __init__(self,script,dir="."):
    Package.__init__(self,'autoconf',script,dir)

  def setup(self,builddir):
    possible_opts=[
      ("--prefix=/usr",         "\s--prefix=PREFIX\s","--prefix not supported"),
      ("--sysconfdir=/etc",     "\s--sysconfdir=DIR\s","--sysconfdir not supported"),
      ("--libexecdir=/usr/lib", "\s--libexecdir=DIR\s","--libexecdir not supported"),
      ("--localstatedir=/var",  "\s--localstatedir=DIR\s","--localstatedir not supported"),
      ("--enable-shared",       "\s--enable-shared\s",""),
      ("--test",                "\s--test\s",""),
      ]
    cmdline=[os.path.join(self.conf_dir,self.conf_script)]
    cmdline.extend(multigrep(os.path.join(self.conf_dir,self.conf_script),possible_opts))
    builddir.command(cmdline)

class PythonPackage(Package):
  def __init__(self,script,dir="."):
    Package.__init__(self,'python',script,dir)

  def setup(self,builddir):
    pass

  def build(self,builddir):
    builddir.command(['python',self.conf_script,'build'])

  def install(self,builddir):
    builddir.command(['python',self.conf_script,'install','--root',builddir.get_destdir()])

class BuildDir:
  def __init__(self,start_dir=None):
    self.debug=False;
    self.nn_root = None
    self.meta={}

    self.exec_env={}

    self.conf_script=None
    self.conf_file=None
    self.conf_dir="."
    self.conf_type=None
    self.conf_opts=[]
    self.pkg = None

    if start_dir and os.path.isdir(os.path.join(start_dir,'.nnpkg')):
      self.nn_root=start_dir

    if not self.nn_root:
      check_dir = os.getcwd()
      while len(check_dir)>1:
        if os.path.isdir(os.path.join(check_dir,'.nnpkg')):
          self.nn_root=check_dir
          break
        if os.path.exists(os.path.join(check_dir,'.cxpkg')):
          self.nn_root=check_dir
          os.mkdir(os.path.join(check_dir,'.nnpkg'))
          break

        check_dir = os.path.split(check_dir)[0]

    with open(os.path.join(check_dir,'.cxpkg')) as f:
      for l in f:
        res = re.match("([A-Z]+)=(.*?)\r?\n?$",l)
        if res:
          self.meta[res.group(1)]=res.group(2)
          print "meta",res.group(1),res.group(2)
#meta:
#PKG=sqlite
#PKGNAM=sqlite3
#PKGVER=3.8.2
#PKGVND=
#PKGCAT=

    if self.nn_root:
      test_script = "%s/configure"%(self.nn_root,)
      if os.path.isfile(test_script):
        self.pkg = AutoconfPackage("configure")
      else:
        test_script = "%s/setup.py"%(self.nn_root,)
        if os.path.isfile(test_script):
          self.pkg = PythonPackage("setup.py")
#          self.conf_script=test_script;
#          self.conf_file="setup.py"
#          self.conf_type="python"

  def get_root(self):
    return self.nn_root

  def get_destdir(self):
    return os.path.join(self.nn_root,'ROOT')

  def set_debug(self,debug):
    self.debug=debug

  def command(self,cmd,vars=None):
    if vars and len(vars)>0:
      for v in vars:
        (name,line)=v.split("=",1)
        if name not in self.exec_env or line != self.exec_env[name]:
          l = os.path.expandvars(line)
          self.exec_env[name]=l
          os.environ[name]=l
          print "! export",v
    if self.debug:
      print "!"," ".join(cmd)
  #   print "!"," ".join([os.path.expandvars(c) for c in cmd])
      subprocess.check_call([os.path.expandvars(c) for c in cmd])

  def setup(self):
    self.pkg.setup(self);

  def build(self):
    self.pkg.build(self);

  def install(self):
    self.pkg.install(self);
