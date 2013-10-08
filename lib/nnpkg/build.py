import os,sys,subprocess
import re,shlex

def confregex(opts):
  res=[]
  for opt in opts:
    diropt=re.match("^\!?(.*)=(/.*)$",opt)
    if diropt: res.append(r'(\s*%s=[A-Z]+\s)'%(diropt.group(1),))
    else:
      enopt=re.match("^\!?--(en|dis)able-(.*)($|=)",opt)
      if enopt: res.append(r'(\s*--(en|dis)able-%s(\s|\[|=))'%(enopt.group(2),))
      else:
        wopt = re.match("^\!?--with(|out)-(.*)$",opt)
        if wopt: res.append(r'(\s*--with(|out)-%s\s)'%(wopt.group(2),))
        else:
          varopt=re.match("^\!?(.*?)\s*=\s*(.*)$",opt)
          if varopt: res.append(r'(\s*%s=[A-Z]+\s)'%(varopt.group(1),))
          else:
            longopt=re.match("^\!?--([a-z0-9-]+)$",opt)
            if longopt: res.append(r'(\s+--%s(\s|=))'%(longopt.group(1),))
            else: res.append('((?!x)x)')
  return res

def makeregex(targets):
  res = []
  for t in targets:
    opt=re.match(r"\!?\s*(.*)\s*=\s*(.*)\s*",t)
    if opt: res.append(r'^\s*%s\s*='%(opt.group(1),))
    else: res.append(r'((^|[^#:]+\s)%s(:|\s+[^#:]*:))'%(t,))
  return res

def grep_all(tosearch,files):
  xfound={}
  if re.match("(^|.*/|.*\.)([Mm]ake.*)",files[0]):
    look=makeregex(tosearch)
  else:
    look=confregex(tosearch)
  re_compiled = re.compile("|".join(look))
  for fn in files:
    try:
#     print "LOOK","|".join(look)
      with open(fn) as f:
        for l in f:
          res = re_compiled.search(l)
          if res:
            for opt_re,opt in zip(look,tosearch):
              if re.search(opt_re,l):
                # possibly overwriting later occurrences intentionally
                xfound[opt_re]=opt
    except (OSError, IOError):
      pass

  res=[]
  for opt_re,opt in zip(look,tosearch):
    if opt_re in xfound:
      if "!" not in xfound[opt_re]:
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
  """
  ************************************************
  A generic package.
  For many purposes, it needs to be subclassed.
  ************************************************
  """
  def __init__(self,type,script,dir="."):
    self.conf_script=script
    self.conf_dir=dir
    self.conf_type=type

  def setup(self,builddir):
    if re.match('bzip2',builddir.meta['PKG']):
      pass
    else:
      raise "Can't configure an unknown package!"

  def build(self,builddir):
    if re.match('attr|acl',builddir.meta['PKG']):
      builddir.install_test.append("install-dev install-lib")
      builddir.install_test.append("!INSTALL=")
      builddir.make_files.append('include/buildmacros')

    if re.match('adns',builddir.meta['PKG']):
      builddir.make_files.append('settings.make')

    if re.match('bzip2',builddir.meta['PKG']):
      builddir.build_test.append("CFLAGS=$CFLAGS")
      builddir.install_test.append("PREFIX=$ROOT/usr LDFLAGS=$LDFLAGS")

    if re.match('git',builddir.meta['PKG']):
      builddir.build_test.append("prefix=/usr")
      builddir.build_test.append("CFLAGS=$CFLAGS")
      builddir.install_test.append("prefix=/usr")
      builddir.install_test.append("CFLAGS=$CFLAGS")

    if re.match('openldap',builddir.meta['PKG']):
      builddir.build_test = ["depend all"]

    cmdline=["make"]
    possible_targets=shlex.split(" ".join(builddir.build_test))
    cmdline.extend(grep_all(possible_targets,builddir.make_files))
    builddir.command(cmdline,[],'build')

  def install(self,builddir):
    if re.match('tig',builddir.meta['PKG']):
      builddir.install_test.append("install-doc-man")

    if isinpath('cxroot'):
      cmdline=['cxroot','$ROOT']
    else:
      cmdline=[]
    cmdline.extend(["make","DESTDIR=$ROOT"])

    possible_targets=shlex.split(" ".join(builddir.install_test))
    cmdline.extend(grep_all(possible_targets,builddir.make_files))
    builddir.command(cmdline,["ROOT=%s"%(builddir.get_destdir())],'install')

class CmakePackage(Package):
  """
  ************************************************
  How to setup build/install a cmake package.
  ************************************************
  """
  def __init__(self,script,dir="."):
    Package.__init__(self,'cmake',script,dir)

  def setup(self,builddir):
    cmd=['cmake']
    cmd.extend(builddir.cmake_test)
    cmd.extend(".")
    builddir.command(cmd,[],'build')

class JamPackage(Package):
  """
  ************************************************
  How to setup build/install Boost as a Jam package.
  ************************************************
  """
  def __init__(self,script,dir="."):
    Package.__init__(self,'jam',script,dir)

  def setup(self,builddir):
    env=[]
    for v in sorted(builddir.env.iterkeys()):
      env.append("%s=%s"%(v,builddir.env[v]))
    builddir.command(['sh','bootstrap.sh'],env,'setup')

  def build(self,builddir):
    builddir.command(['./bjam','release','debug','threading=multi','toolset=gcc','--layout=tagged'],[],'build')

  def install(self,builddir):
    builddir.command(['./bjam','install','--layout=tagged','--prefix=%s'%(builddir.get_destdir(),)],[],'install')

class AutoconfPackage(Package):
  """
  ************************************************
  How to setup an autoconf-like package.
  ************************************************
  """
  def __init__(self,script,dir="."):
    Package.__init__(self,'autoconf',script,dir)

  def setup(self,builddir):
    if self.conf_script:
      builddir.conf_files.append(self.conf_script)

      # save help output for flag changes
      help_option = grep_all(['--help'],[self.conf_script])
      if len(help_option)>0:
        builddir.command([os.path.join(self.conf_dir,self.conf_script),'--help'],[],'help')

    if re.match('bash',builddir.meta['PKG']):
      ## flavour minimal vs none
      builddir.conf_test.append("--with-installed-readline --with-curses")

    if re.match('e2fsprogs',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-dynamic-e2fsck --enable-fsck --enable-blkid-devmapper --enable-elf-shlibs")
      builddir.conf_test.append("--disable-libblkid --disable-libuuid --disable-uuidd")
      builddir.install_test.append("install-libs")
      builddir.env['DEVMAPPER_LIBS']='-ldevmapper  -lpthread'
      builddir.env['STATIC_DEVMAPPER_LIBS']='-ldevmapper  -lpthread'
      builddir.env['LDFLAG_STATIC']=''

    if re.match('gmp',builddir.meta['PKG']):
      builddir.env['CFLAGS']="-Os -fomit-frame-pointer -fexceptions -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64"
      builddir.env['CXXFLAGS']="-Os -fomit-frame-pointer -fexceptions -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64"
      builddir.conf_test.append("--enable-cxx --enable-mpfr --enable-mpbsd")
      ## flavour i386 vs i686
      builddir.conf_test.append("--build=i386-pc-linux-gnu")


    if re.match('gnupg',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-gpgtar --libexecdir=/usr/lib/gnupg")

    if re.match('groff',builddir.meta['PKG']):
      builddir.conf_test.append("--with-appresdir=/etc/X11/app-defaults")

    if re.match('LVM2',builddir.meta['PKG']):
      builddir.conf_test.append("--sbindir=/sbin --libdir=/lib --exec-prefix= --enable-static_link")
      builddir.make_files.append('make.tmpl')

    if re.match('lzip',builddir.meta['PKG']):
      builddir.conf_test.append("CXXFLAGS=$CXXFLAGS")
      builddir.conf_test.append("LDFLAGS=$LDFLAGS")

    if re.match('openldap',builddir.meta['PKG']):
      builddir.conf_test.append("--libexecdir=/usr/sbin --localstatedir=/var/lib/openldap-data")
      builddir.conf_test.append("--enable-ipv6 --enable-rewrite --enable-bdb --enable-hdb --enable-meta --enable-ldap --enable-overlays")
      builddir.conf_test.append("--without-cyrus-sasl --disable-spasswd --disable-perl")

    if re.match('pcre',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-utf8 --enable-unicode-properties --enable-pcre16 --enable-jit")
      builddir.conf_test.append("--enable-pcregrep-libz --enable-pcregrep-libbz2")

    if re.match('tar',builddir.meta['PKG']):
      builddir.conf_test.append("--libexecdir=/etc")
      builddir.env['tar_cv_path_RSH']='/usr/bin/ssh'

    if re.match('vim',builddir.meta['PKG']):
      builddir.conf_test.append("--disable-selinux --enable-pythoninterp --enable-cscope --enable-multibyte --enable-gui=gtk2")
      builddir.conf_files.append("src/auto/configure")
      ## flavour nogui (vs gtk2)
#     builddir.conf_test.append("--disable-gui --without-x --disable-xim")

    if re.match('zsh',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-maildir-support --with-curses-terminfo --disable-gdbm")

    env=[]
    for v in sorted(builddir.env.iterkeys()):
      env.append("%s=%s"%(v,builddir.env[v]))
    possible_opts=shlex.split(" ".join(builddir.conf_test))
    cmdline=[os.path.join(self.conf_dir,self.conf_script)]
    cmdline.extend(grep_all(possible_opts,builddir.conf_files))
    builddir.command(cmdline,env,'setup')

class PythonPackage(Package):
  """
  ************************************************
  How to setup build/install a Python package.
  ************************************************
  """
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
    self.cmake_test=["-DCMAKE_INSTALL_PREFIX=/usr"]
    self.build_test=["all"]
    self.install_test=["install","INSTALL=install"]
    self.env={}
    self.env['CC']="gcc"
    self.env['CFLAGS']="-Os -fno-asynchronous-unwind-tables -fomit-frame-pointer -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64"
    self.env['CXX']="g++"
    self.env['CXXFLAGS']="-Os -fomit-frame-pointer -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64"
    self.env['LDFLAGS']="-s -Wl,--as-needed"
    self.conf_files=[]
    self.make_files=['Makefile',]

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

    try:
      with open(os.path.join(check_dir,'.cxpkg')) as f:
        for l in f:
          res = re.match("([A-Z]+)=(.*?)\r?\n?$",l)
          if res:
            self.meta[res.group(1)]=res.group(2)
            print "meta",res.group(1),res.group(2)
    except (OSError, IOError):
      print "Cannot find .cxpkg"
      sys.exit(1)
#meta: PKG=sqlite PKGNAM=sqlite3 PKGVER=3.8.2 PKGVND= PKGCAT=

    if self.nn_root:
      test_script= "%s/CMakeLists.txt"%(self.nn_root,)
      if os.path.isfile(test_script):
        self.pkg = CmakePackage("CMakeListst.txt")
      else:
        test_script = "%s/configure"%(self.nn_root,)
        if os.path.isfile(test_script):
          self.pkg = AutoconfPackage("configure")
        else:
          test_script = "%s/setup.py"%(self.nn_root,)
          if os.path.isfile(test_script):
            self.pkg = PythonPackage("setup.py")
          else:
            test_script = "%s/boost-build.jam"%(self.nn_root,)
            if os.path.isfile(test_script):
              self.pkg = JamPackage("Jamroot")
            else:
              self.pkg = Package("unknown",None)

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

    try:
      cmd_proc = subprocess.Popen([os.path.expandvars(c) for c in cmd],stdout=subprocess.PIPE)
      while True:
        l = cmd_proc.stdout.readline()
        if log_proc: log_proc.stdin.write(l)
        print l,
        if len(l)<=0: break
      if log_proc:
        log_proc.stdin.close()
    except KeyboardInterrupt:
      if cmd_proc: cmd_proc.terminate()
      if log_proc: log_proc.terminate()
    if log_proc: log_proc.wait()
    if cmd_proc: cmd_proc.wait()
    if cmd_proc.returncode:
      sys.exit(1)
    return cmd_proc.returncode

  def setup(self):
    self.pkg.setup(self);

  def build(self):
    self.pkg.build(self);

  def install(self):
    self.pkg.install(self);
