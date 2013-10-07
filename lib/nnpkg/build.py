import os
import subprocess
import re

def confregex(opts):
  res=[]
  for opt in opts:
    diropt=re.match("^(.*)=(/.*)$",opt)
    if diropt: res.append(r'(^\s*%s=[A-Z]+\s)'%(diropt.group(1),))
    else:
      enopt=re.match("^--(en|dis)able-(.*)($|=)",opt)
      if enopt: res.append(r'(^\s*--(en|dis)able-%s(\s|\[|=))'%(enopt.group(2),))
      else:
        wopt = re.match("^--with(|out)-(.*)$",opt)
        if wopt: res.append(r'(^\s*--with(|out)-%s\s)'%(wopt.group(2),))
        else:
          res.append('((?!x)x)')
  return res

def makeregex(targets):
  res = []
  for t in targets:
    opt=re.match(r"\s*(.*)\s*=\s*(.*)\s*",t)
    if opt: res.append(r'^\s*%s\s*='%(opt.group(1),))
    else: res.append(r'((^|[^#:]+\s)%s(:|\s+[^#:]*:))'%(t,))
  return res

def grep_all(tosearch,fn):
  xfound={}
  if re.match("(^|/)[Mm]ake.*",fn):
    look=makeregex(tosearch)
  else:
    look=confregex(tosearch)
  try:
#   print "LOOK","|".join(look)
    re_compiled = re.compile("|".join(look))
    with open(fn) as f:
      for l in f:
        res = re_compiled.search(l)
        if res:
          for opt_re,opt in zip(look,tosearch):
            if re.search(opt_re,l):
#              print "[%s]=%s"%(opt_re,opt,)
              # possibly overwriting later occurrences intentionally
              xfound[opt_re]=opt
  except (OSError, IOError):
    pass
  res=[]
  for opt_re,opt in zip(look,tosearch):
    if opt_re in xfound:
      res.append(xfound[opt_re])
      del xfound[opt_re]

  return res

def isinpath(exe):
  for d in os.getenv('PATH','').split(":"):
    xpath = os.path.join(d,exe)
    if os.path.isfile(xpath) and os.access(xpath,os.X_OK):
      return True
  return False

class Package(object):
  def __init__(self,type,script,dir="."):
    self.conf_script=script
    self.conf_dir=dir
    self.conf_type=type
    self.conf_file=None

  def setup(self,builddir):
    raise "Can't configure an unknown package!"

  def build(self,builddir):
    if re.match('openldap',builddir.meta['PKG']):
      builddir.build_test = ["depend all"]

    cmdline=["make"]
    possible_targets=(" ".join(builddir.build_test).split(" "))
    cmdline.extend(grep_all(possible_targets,"Makefile"))
    builddir.command(cmdline,[],'build')

  def install(self,builddir):
    if re.match('tig',builddir.meta['PKG']):
      builddir.install_test.append("install-doc-man")

    if isinpath('cxroot'):
      cmdline=['cxroot','$ROOT']
    else:
      cmdline=[]
    cmdline.extend(["make","DESTDIR=$ROOT","INSTALL=install"])

    possible_targets=(" ".join(builddir.install_test).split(" "))
    cmdline.extend(grep_all(possible_targets,"Makefile"))
    builddir.command(cmdline,["ROOT=%s"%(builddir.get_destdir())],'install')

class AutoconfPackage(Package):
  def __init__(self,script,dir="."):
    Package.__init__(self,'autoconf',script,dir)

  def setup(self,builddir):
    if re.match('openldap',builddir.meta['PKG']):
      builddir.conf_test.append("--libexecdir=/usr/sbin --localstatedir=/var/lib/openldap-data")
      builddir.conf_test.append("--enable-ipv6 --enable-rewrite --enable-bdb --enable-hdb --enable-meta --enable-ldap --enable-overlays")
      builddir.conf_test.append("--without-cyrus-sasl --disable-spasswd --disable-perl")

    possible_opts=(" ".join(builddir.conf_test).split(" "))
    cmdline=[os.path.join(self.conf_dir,self.conf_script)]
    cmdline.extend(grep_all(possible_opts,self.conf_script))
    builddir.command(cmdline,[],'setup')

class PythonPackage(Package):
  def __init__(self,script,dir="."):
    Package.__init__(self,'python',script,dir)

  def setup(self,builddir):
    pass

  def build(self,builddir):
    builddir.command(['python',self.conf_script,'build'],[],'build')

  def install(self,builddir):
    builddir.command(['python',self.conf_script,'install','--root',builddir.get_destdir()],[],'install')

class BuildDir:
  def __init__(self,start_dir=None):
    self.debug=False;
    self.nn_root = None
    self.meta={}
    self.conf_test=["--prefix=/usr --sysconfdir=/etc --libexecdir=/usr/lib --localstatedir=/var --enable-shared"]
    self.build_test=["all"]
    self.install_test=["install"]
#CFLAGS=-Os -fno-asynchronous-unwind-tables -fomit-frame-pointer -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64
#CXXFLAGS=-Os -fomit-frame-pointer -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64
#LDFLAGS=-s -Wl,--as-needed

    self.exec_env={}

    self.conf_script=None
    self.conf_file=None
    self.conf_dir="."
    self.conf_type=None
    self.conf_opts=[]
    self.pkg = None

    self.do_multilog = isinpath('multilog')

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

  def get_root(self):
    return self.nn_root

  def get_destdir(self):
    return os.path.join(self.nn_root,'ROOT')

  def set_debug(self,debug):
    self.debug=debug

  def command(self,cmd,vars=None,logto=None):
    if self.do_multilog and logto and not self.debug:
      logdir = os.path.join(self.nn_root,'.nnpkg',logto)
      try: os.mkdir(logdir)
      except: pass
      log_proc = subprocess.Popen(['multilog','t','s999999','n25',logdir],stdin=subprocess.PIPE)
    else: log_proc = None

    if vars and len(vars)>0:
      for v in vars:
        (name,line)=v.split("=",1)
        if name not in self.exec_env or line != self.exec_env[name]:
          l = os.path.expandvars(line)
          self.exec_env[name]=l
          os.environ[name]=l
          if log_proc: log_proc.stdin.write("! export %s\n"%(v,))
          print "! export",v

    if log_proc: log_proc.stdin.write("! %s\n"%(" ".join([os.path.expandvars(c) for c in cmd]),))
    print "!"," ".join(cmd)

    cmd_proc = subprocess.Popen([os.path.expandvars(c) for c in cmd],stdout=subprocess.PIPE)
    while True:
      l = cmd_proc.stdout.readline()
      if log_proc: log_proc.stdin.write(l)
      print l,
      if len(l)<=0: break
    if log_proc:
      log_proc.stdin.close()
      log_proc.wait()
    cmd_proc.wait()
    return cmd_proc.returncode

  def setup(self):
    self.pkg.setup(self);

  def build(self):
    self.pkg.build(self);

  def install(self):
    self.pkg.install(self);
