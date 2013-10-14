import os,sys,subprocess
import re,shlex

def confregex(opts):
  res=[]
  for opt in opts:
    diropt=re.match("^\!?(.*)=(/.*)$",opt)
    if diropt: res.append(r'(\s*%s=[A-Z]+\s)'%(diropt.group(1),))
    else:
      enopt=re.match("^\!?--(en|dis)able-(.*?)($|=)",opt)
      if enopt: res.append(r'(\s*--(en|dis)able-%s(\s|\[|=))'%(enopt.group(2),))
      else:
        wopt = re.match("^\!?--with(|out)-([a-z0-9-]+).*",opt)
        if wopt: res.append(r'(\s*--with(|out)-%s(\s|=))'%(wopt.group(2),))
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

def grep_all(tosearch,files,where=None):
  xfound={}
  if re.match("(^|.*/|.*\.)([Mm]ake.*)",files[0]):
    look=makeregex(tosearch)
  else:
    look=confregex(tosearch)
  re_compiled = re.compile("|".join(look))

  if where:
    oldcwd = os.getcwd()
    os.chdir(where)
  else:
    oldcwd = None

  for fn in files:
    try:
#     print "LOOK:","|".join(look),fn
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

  if oldcwd: os.chdir(oldcwd)
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
      builddir.make_test.append("CFLAGS=$CFLAGS")
      builddir.install_test.append("PREFIX=$ROOT/usr LDFLAGS=$LDFLAGS")

    if re.match('git',builddir.meta['PKG']):
      builddir.make_test.append("prefix=/usr")
      builddir.make_test.append("CFLAGS=$CFLAGS LDFLAGS=$LDFLAGS")
      builddir.install_test.append("prefix=/usr")

    if re.match('openldap',builddir.meta['PKG']):
      builddir.make_test = ["depend all"]

    cmdline=["make"]
    possible_targets=shlex.split(" ".join(builddir.make_test))
    cmdline.extend(grep_all(possible_targets,builddir.make_files,builddir.get_use_dir()))
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
    cmdline.extend(grep_all(possible_targets,builddir.make_files,builddir.get_use_dir()))
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
    cmd.extend(shlex.split(" ".join(builddir.cmake_test)))
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
    builddir.command(['./bjam','install','--layout=tagged','--prefix=$ROOT/usr',],["ROOT=%s"%(builddir.get_destdir(),)],'install')

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
        conf_path = builddir.rel_to_use(self.conf_script)
        builddir.command(['sh',conf_path,'--help'],[],'help')

    # set defaults for X packages
    if builddir.meta['PKGVND'] in ['X11']:
      builddir.conf_test.append("--libexecdir=/usr/X11/lib --bindir=/usr/X11/bin --libdir=/usr/X11/lib")
      builddir.conf_test.append("--sysconfdir=/etc/X11 --mandir=/usr/X11/man --includedir=/usr/X11/include")

    if re.match('apr',builddir.meta['PKG']):
      builddir.conf_test.append("--with-installbuilddir=/usr/share/apr-1/build")
      builddir.env['CC']="gcc -std=gnu99"
    if re.match('apr-util',builddir.meta['PKG']):
      builddir.conf_test.append("--with-apr=/usr --with-openssl=/usr --with-sqlite3=/usr --with-expat=/usr --with-berkeley-db=/usr")
      builddir.conf_test.append("--with-crypto --with-ldap")
      builddir.env['CC']="gcc -std=gnu99"

    if re.match('bash',builddir.meta['PKG']):
      ## flavour minimal vs none
      builddir.conf_test.append("--with-installed-readline --with-curses")

    if builddir.meta['PKG'] == 'cairo':
      builddir.conf_test.append("--enable-gl --enable-drm --enable-xlib-xcb")

    if re.match('cloog',builddir.meta['PKG']):
      builddir.conf_test.append("--with-isl=system")

    if re.match('cups',builddir.meta['PKG']):
      builddir.conf_test.append("--with-cups-user=cups --with-cups-group=cups --disable-pam --disable-slp")
      builddir.make_files.append('Makedefs')
      builddir.install_test.append("BUILDROOT=$ROOT")

    if re.match('db',builddir.meta['PKG']):
      builddir.use_dir('BUILD')
      builddir.conf_test.append("--enable-tcl --enable-cxx --enable-compat185 --enable-java --with-tcl=/usr/lib")
      builddir.install_test.append("docdir=/usr/share/doc/db")

    if builddir.meta['PKG'] == 'doxygen':
      builddir.conf_add.append("--prefix /usr --docdir /usr/share/doc")
      builddir.make_files.append("src/Makefile.libdoxycfg")
      builddir.env['CFLAGS']="-Os -fno-asynchronous-unwind-tables -fomit-frame-pointer -fno-exceptions -fno-rtti -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64"
      builddir.make_test.append("CFLAGS=$CFLAGS CXXFLAGS=$CFLAGS")
      builddir.install_test.append("!INSTALL=/usr")

    if re.match('e2fsprogs',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-dynamic-e2fsck --enable-fsck --enable-blkid-devmapper --enable-elf-shlibs")
      builddir.conf_test.append("--disable-libblkid --disable-libuuid --disable-uuidd")
      builddir.install_test.append("install-libs")
      builddir.env['DEVMAPPER_LIBS']='-ldevmapper  -lpthread'
      builddir.env['STATIC_DEVMAPPER_LIBS']='-ldevmapper  -lpthread'
      builddir.env['LDFLAG_STATIC']=''

    if re.match('freetype',builddir.meta['PKG']):
      builddir.conf_files.append("builds/unix/configure")
      builddir.make_files.append("builds/unix/install.mk")

    if re.match('gamin',builddir.meta['PKG']):
      builddir.conf_test.append("--libexecdir=/usr/sbin")
      builddir.env['CFLAGS']="-Os -fomit-frame-pointer -fexceptions -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64 -DG_CONST_RETURN=const"

    if re.match('gmp',builddir.meta['PKG']):
      builddir.env['CFLAGS']="-Os -fomit-frame-pointer -fexceptions -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64"
      builddir.env['CXXFLAGS']="-Os -fomit-frame-pointer -fexceptions -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64"
      builddir.conf_test.append("--enable-cxx --enable-mpfr --enable-mpbsd")
      ## flavour i386 vs i686
      builddir.conf_test.append("--build=i386-pc-linux-gnu")

    if re.match('gnupg',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-gpgtar --libexecdir=/usr/lib/gnupg")

    if re.match('gnutls',builddir.meta['PKG']):
      builddir.conf_test.append("--with-lzo")

    if re.match('groff',builddir.meta['PKG']):
      builddir.conf_test.append("--with-appresdir=/etc/X11/app-defaults")

    if re.match('httpd',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-layout=RedHat --exec-prefix=/usr --libexecdir=/usr/lib/apache/so")
      builddir.conf_test.append("--sysconfdir=/etc/apache --mandir=/usr/share/man/apache --datadir=/usr/share/apache")
      builddir.conf_test.append("--enable-so --enable-ssl --enable-mods-shared=all")
      builddir.conf_test.append("--enable-deflate --enable-proxy")
      builddir.conf_test.append("--with-ldap --enable-authnz-ldap --enable-ldap")
      builddir.conf_test.append("--enable-dbd --enable-authn-dbd")
      builddir.conf_test.append("--enable-authz-dbm --enable-authn-dbm")
      builddir.conf_test.append("--enable-cache --enable-file_cache --enable-disk_cache --enable-mem_cache")
      builddir.conf_test.append("--enable-charset_lite")
      builddir.conf_test.append("--enable-authn-dbm --enable-authz-dbm --with-berkeley-db --with-dbm=db")
      builddir.conf_test.append("--with-pcre --with-devrandom --with-mpm=prefork")
      builddir.make_files.append('build/rules.mk')
      builddir.env['CC']="gcc -std=gnu99"

    if re.match('icu4c',builddir.meta['PKG']):
      builddir.use_dir('BUILD')

    if re.match('libxml2',builddir.meta['PKG']):
      builddir.conf_test.append("--with-icu")

    if re.match('LVM2',builddir.meta['PKG']):
      builddir.conf_test.append("--sbindir=/sbin --libdir=/lib --exec-prefix= --enable-static_link")
      builddir.make_files.append('make.tmpl')

    if re.match('lzip',builddir.meta['PKG']):
      builddir.conf_test.append("CXXFLAGS=$CXXFLAGS")
      builddir.conf_test.append("LDFLAGS=$LDFLAGS")

    if re.match('neon',builddir.meta['PKG']):
      builddir.conf_test.append("--with-ssl=openssl")

    if re.match('openldap',builddir.meta['PKG']):
      builddir.conf_test.append("--libexecdir=/usr/sbin --localstatedir=/var/lib/openldap-data")
      builddir.conf_test.append("--enable-ipv6 --enable-rewrite --enable-bdb --enable-hdb --enable-meta --enable-ldap --enable-overlays")
      builddir.conf_test.append("--without-cyrus-sasl --disable-spasswd --disable-perl")

    if re.match('pcre',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-utf8 --enable-unicode-properties --enable-pcre16 --enable-jit")
      builddir.conf_test.append("--enable-pcregrep-libz --enable-pcregrep-libbz2")

    if re.match('subversion',builddir.meta['PKG']):
      builddir.install_test.append("install-swig-rb install-swig-py install-swig-pl")
      builddir.env['CC']="gcc -std=gnu99"

    if re.match('tar',builddir.meta['PKG']):
      builddir.conf_test.append("--libexecdir=/etc")

    if re.match('LVM2',builddir.meta['PKG']):
      builddir.conf_test.append("--sbindir=/sbin --libdir=/lib --exec-prefix= --enable-static_link")
      builddir.make_files.append('make.tmpl')

    if re.match('lzip',builddir.meta['PKG']):
      builddir.conf_test.append("CXXFLAGS=$CXXFLAGS")
      builddir.conf_test.append("LDFLAGS=$LDFLAGS")

    if re.match('mpfr',builddir.meta['PKG']):
      builddir.env['CFLAGS']="-Os -fomit-frame-pointer -fexceptions -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64"
      builddir.env['CXXFLAGS']="-Os -fomit-frame-pointer -fexceptions -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64"
      builddir.conf_test.append("--build=i386-pc-linux-gnu")

    if re.match('openldap',builddir.meta['PKG']):
      builddir.conf_test.append("--libexecdir=/usr/sbin --localstatedir=/var/lib/openldap-data")
      builddir.conf_test.append("--enable-ipv6 --enable-rewrite --enable-bdb --enable-hdb --enable-meta --enable-ldap --enable-overlays")
      builddir.conf_test.append("--without-cyrus-sasl --disable-spasswd --disable-perl")

    if builddir.meta['PKG'] == 'p11-kit':
      builddir.conf_test.append("--without-trust-paths")

    if re.match('pcre',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-utf8 --enable-unicode-properties --enable-pcre16 --enable-jit")
      builddir.conf_test.append("--enable-pcregrep-libz --enable-pcregrep-libbz2")

    if re.match('ruby',builddir.meta['PKG']):
      builddir.make_files.append("common.mk")

    if re.match('tar',builddir.meta['PKG']):
      builddir.conf_test.append("--libexecdir=/etc")
      builddir.env['tar_cv_path_RSH']='/usr/bin/ssh'

    if re.match('tcl|tk',builddir.meta['PKG']):
      builddir.use_dir('BUILD')
      builddir.conf_test.append("--without-tzdata")
      builddir.install_test.append("install-private-headers")

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

    cmdline=['sh',builddir.rel_to_use(self.conf_script)]
    possible_opts=shlex.split(" ".join(builddir.conf_test))
    fixed_opts=shlex.split(" ".join(builddir.conf_add))
    cmdline.extend(fixed_opts)
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

class SconsPackage(Package):
  """
  ************************************************
  How to setup build/install a SConstruct package.
  ************************************************
  """
  def __init__(self,script,dir="."):
    Package.__init__(self,'scons',script,dir)

  def setup(self,builddir):
    builddir.command(['scons','--help'],[],'help')

  def build(self,builddir):
    if re.match('serf',builddir.meta['PKG']):
      builddir.scons_test.append("APR=/usr APU=/usr OPENSSL=/usr CFLAGS=$CFLAGS LINKFLAGS=$LDFLAGS")

    cmd=['scons']
    cmd.extend(shlex.split(" ".join(builddir.scons_test)))
    builddir.command(cmd,[],'build')

  def install(self,builddir):
    builddir.command(['scons','PREFIX=$ROOT/usr','install'],["ROOT=%s"%(builddir.get_destdir(),)],'install')

class BuildDir:
  def __init__(self,start_dir=None):
    self.debug=False;
    self.nn_root = None
    self.cwd = None
    self.cwd_use = None
    self.meta={}
    self.conf_test=["--prefix=/usr --sysconfdir=/etc --libexecdir=/usr/lib --localstatedir=/var --enable-shared"]
    self.conf_add=[]
    self.make_test=["all"]
    self.scons_test=["PREFIX=/usr"]
    self.cmake_test=["-DCMAKE_INSTALL_PREFIX=/usr"]
    self.install_test=["install","INSTALL=install"]
    self.env={}
    self.env['CC']="gcc"
    self.env['CFLAGS']="-Os -fno-asynchronous-unwind-tables -fomit-frame-pointer -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64"
    self.env['CXX']="g++"
    self.env['CXXFLAGS']="-Os -fomit-frame-pointer -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64"
    self.env['LDFLAGS']="-s -Wl,--as-needed"
    self.conf_files=[]
    self.make_files=['Makefile','GNUmakefile',]

    self.exec_env={}

    self.conf_script=None
    self.conf_file=None
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

    # everything GNU
    if self.check_file('configure'):
      self.pkg = AutoconfPackage('./configure')
    # Berkeley db
    elif self.check_file('dist/configure'):
      self.pkg = AutoconfPackage('dist/configure')
    # tcl/tk
    elif self.check_file('unix/configure'):
      self.pkg = AutoconfPackage('unix/configure')
    # ICU4C
    elif self.check_file('source/configure'):
      self.pkg = AutoconfPackage('source/configure')
    elif self.check_file('setup.py'):
      self.pkg = PythonPackage('setup.py')
    elif self.check_file('Jamroot'):
      self.pkg = JamPackage('Jamroot')
    # Some packages using cmake and configure use cmake for other platforms
    # and less Unixy features - no symbol versioning, no tools, no .la files.
    elif self.check_file('CMakeLists.txt'):
      self.pkg = CmakePackage("CMakeListst.txt")
    elif self.check_file('SConstruct'):
      self.pkg = SconsPackage('SConstruct')
    else:
      self.pkg = Package("Unknown",None)

    os.chdir(self.nn_root)
    self.cwd = self.nn_root

  def get_root_path(self):
    return self.nn_root

  def get_destdir(self):
    return os.path.join(self.nn_root,'ROOT')

  def check_file(self,fn):
    return os.path.isfile(os.path.join(self.nn_root,fn))

  # dir to use for command()
  def use_dir(self,path):
    self.cwd_use = path

  def get_use_dir(self):
    if self.cwd_use:
      return os.path.relpath(self.cwd_use,self.nn_root)
    else:
      return os.path.relpath(self.cwd,self.nn_root)

  # relative path, relative to the "use" above (or the cwd if already used)
  def rel_to_use(self,path):
    if self.cwd_use:
      return os.path.relpath(path,os.path.join(self.nn_root,self.cwd_use))
    return os.path.relpath(path,os.path.join(self.nn_root,self.cwd))

  def set_debug(self,debug):
    self.debug=debug

  def command(self,cmd,vars=None,logto=None):
    os.chdir(self.nn_root)
    if self.do_multilog and logto and not self.debug:
      logdir = os.path.join('.nnpkg',logto)
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

    os.chdir(self.cwd)
    if self.cwd_use:
      rel_dir = os.path.relpath(self.cwd_use,self.cwd)
      if not os.path.exists(self.cwd_use):
        os.mkdir(self.cwd_use)
        if log_proc: log_proc.stdin.write("! mkdir %s\n"%(rel_dir,))
        print "! mkdir %s"%(self.cwd_use,)
      if log_proc: log_proc.stdin.write("! cd %s\n"%(rel_dir,))
      print "! cd %s"%(self.cwd_use,)
      os.chdir(self.cwd_use)
      self.cwd = os.getcwd()
      self.cwd_use = None

    if log_proc: log_proc.stdin.write("! %s\n"%(" ".join([os.path.expandvars(c) for c in cmd]),))
    print "!"," ".join(cmd)

    try:
      cmd_proc = subprocess.Popen([os.path.expandvars(c) for c in cmd],stdout=subprocess.PIPE)
      while True:
        l = cmd_proc.stdout.readline()
        if log_proc: log_proc.stdin.write(l)
        if len(l)<=0: break
        print l,
      if log_proc:
        log_proc.stdin.close()
    except KeyboardInterrupt:
      if cmd_proc: cmd_proc.terminate()
      if log_proc: log_proc.terminate()
    if log_proc: log_proc.wait()
    if cmd_proc: cmd_proc.wait()
    if cmd_proc.returncode:
      sys.exit(1)

    os.chdir(self.nn_root)

    # XXX flag done if necessary
    return 0

  def setup(self):
    self.pkg.setup(self);

  def build(self):
    self.pkg.build(self);

  def install(self):
    self.pkg.install(self);
