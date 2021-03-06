import os,sys,subprocess
import re,shlex

BUILD='i586-pc-linux-gnu'

def confregex(opts):
  res=[]
  for opt in opts:
    diropt=re.match("^\!?\[?(.*)=(/.*)(\]|$)",opt)
    if diropt: res.append(r'(\s*\[?%s[= ])'%(diropt.group(1),));
    else:
      enopt=re.match("^\!?--(en|dis)able-(.*?)($|=.*)",opt)
      if enopt: res.append(r'(\s*--(en|dis)able-%s(\s|\[|=))'%(enopt.group(2),))
      else:
        wopt = re.match("^\!?--with(|out)-([a-z0-9_-]+)(\s.*|=.*)",opt)
        if wopt: res.append(r'(\s*--with(|out)-%s(\s|=))'%(wopt.group(2),))
        else:
          varopt=re.match("^\!?(.*?)\s*=\s*(.*)$",opt)
          if varopt: res.append(r'(\s*%s=[012A-Za-z/]+\s)'%(varopt.group(1),))
          else:
            longopt=re.match("^\!?--([a-z0-9_-]+)$",opt)
            if longopt: res.append(r'(\s+--%s(\s|=))'%(longopt.group(1),))
            else: res.append('((?!x)x)')
  return res

def makeregex(targets):
  res = []
  for t in targets:
    opt=re.match(r"\!?\s*(.*)\s*\??\s*?=\s*(.*)\s*",t)
    #f opt: res.append(r'^\s*%s\s*\??\s*[:?]?='%(opt.group(1),))
    # f opt: res.append(r'\s+%s\s*\??\s*[:?]?='%(opt.group(1),))
    if opt: res.append(r'^\s*%s\s*\??\s*[:?]?='%(opt.group(1),))
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
    if builddir.meta['PKG'] in ['bzip2','libebml','libmatroska','lua','haproxy','btrfs-progs','rhash','pigz','mdadm','lz4','pciutils']:
      pass
    elif builddir.meta['PKG'] in ['botan','Botan']:
      builddir.command(['python','configure.py'],[],'setup')
    elif os.path.exists(os.path.join(builddir.cwd,'Imakefile')):
      builddir.command(['xmkmf','-a'],[],'setup')
    else:
      raise RuntimeError("Can't configure an unknown package!")

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

    if re.match('haproxy',builddir.meta['PKG']):
      builddir.make_test.append("PREFIX=/usr TARGET=linux2628")
      builddir.install_test.append("PREFIX=/usr")

    if re.match('lua',builddir.meta['PKG']):
      builddir.make_test=[]
      builddir.make_test.append("INSTALL_TOP=/usr linux")
      builddir.make_test.append("MYCFLAGS=$CFLAGS")
      builddir.make_files.append('src/Makefile')
      builddir.install_test.append("INSTALL_TOP=/usr")

    if builddir.meta['PKG'] in ['libebml','libmatroska']:
      if os.path.exists(os.path.join(builddir.cwd,'make/linux')):
        builddir.use_dir('make/linux')
      builddir.make_test.append("prefix=/usr WARNINGFLAGS=$CXXFLAGS")
      builddir.install_test.append("prefix=/usr")

    if re.match('mdadm',builddir.meta['PKG']):
      builddir.make_test.append("RUN_DIR=/dev/.adm")
      builddir.install_test.append("RUN_DIR=/dev/.adm")

    if re.match('nspr|nss',builddir.meta['PKG']):
      builddir.make_files.append('config/rules.mk')

    if re.match('pciutils',builddir.meta['PKG']):
      builddir.make_test.append("PREFIX=/usr OPT=-Os")
      builddir.install_test.append("PREFIX=/usr install-lib")

    if re.match('rhash',builddir.meta['PKG']):
      builddir.make_test.append("CFLAGS=$CFLAGS")
      builddir.install_test.append("PREFIX=/usr LDFLAGS=$LDFLAGS")

    # iterate make_files[]?
    if os.path.exists(os.path.join(builddir.cwd,'Makefile')):
      cmdline=["make"]
    elif os.path.exists(os.path.join(builddir.cwd,'GNUmakefile')):
      cmdline=["make"]
    elif os.path.exists(os.path.join(builddir.cwd,'Rakefile')):
      cmdline=["rake"]
    else:
      raise RuntimeError("No Makefile found in "+builddir.cwd)

    possible_targets=shlex.split(" ".join(builddir.make_test))
    cmdline.extend(grep_all(possible_targets,builddir.make_files,builddir.get_use_dir()))
    builddir.command(cmdline,[],'build')

  def install(self,builddir):
    destdir="$ROOT"
    if re.match('tig',builddir.meta['PKG']):
      builddir.install_test.append("install-doc-man")

    if builddir.meta['PKG'] in ['botan','Botan']:
      destdir="$ROOT/usr"

    if re.match('btrfs-progs',builddir.meta['PKG']):
      builddir.install_test.append("prefix=/usr")

    if len(builddir.root_redir)>0 and isinpath(builddir.root_redir[0]):
      cmdline=builddir.root_redir
    else:
      cmdline=[]

    if os.path.exists(os.path.join(builddir.cwd,'Makefile')):
      cmdline.extend(["make","DESTDIR=%s"%(destdir,)])
    elif os.path.exists(os.path.join(builddir.cwd,'GNUmakefile')):
      cmdline.extend(["make","DESTDIR=%s"%(destdir,)])
    elif os.path.exists(os.path.join(builddir.cwd,'Rakefile')):
      cmdline.extend(["rake","DESTDIR=%s"%(destdir,),'install'])
    else:
      raise RuntimeError("No Makefile found in "+builddir.cwd)

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
    if re.match('llvm',builddir.meta['PKG']):
      # llvm wants to do this, but doesn't quite make it
      builddir.env['CFLAGS']=''
      builddir.env['CXXFLAGS']=''
      builddir.env['LDFLAGS']=''
      builddir.use_dir('BUILD')
      builddir.cmake_test.append("-DBUILD_SHARED_LIBS=1")

    if re.match('cfe',builddir.meta['PKG']):
      builddir.env['CFLAGS']=''
      builddir.env['CXXFLAGS']=''
      builddir.env['LDFLAGS']=''
      builddir.use_dir('BUILD')
      builddir.cmake_test.append('-DBUILD_SHARED_LIBS=1 -DCLANG_PATH_TO_LLVM_BUILD=/usr')

    cmd=['cmake']
    cmd.extend(shlex.split(" ".join(builddir.cmake_test)))
    cmd.append(builddir.rel_to_use(builddir.nn_root))
    builddir.command(cmd,[],'setup')

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
    builddir.command(['$SHELL','bootstrap.sh'],env,'setup')

  def build(self,builddir):
    builddir.command(['./bjam','release','debug','threading=multi','toolset=gcc','--layout=tagged','--without-mpi'],[],'build')

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
        builddir.mustsucceed=False
        builddir.command(['$SHELL',conf_path,'--help'],[],'help')

    # set defaults for X packages
    if builddir.meta['PKGVND'] in ['X11'] or builddir.meta['PKGCAT'] in ['X11']:
      builddir.conf_test.append("--libexecdir=/usr/X11/lib --bindir=/usr/X11/bin --libdir=/usr/X11/lib")
      builddir.conf_test.append("--sysconfdir=/etc/X11 --mandir=/usr/X11/man --includedir=/usr/X11/include")

    if re.match('apr',builddir.meta['PKG']):
      builddir.env['CC']="gcc -std=gnu99"
      builddir.conf_test.append("--with-installbuilddir=/usr/share/apr-1/build")

    if re.match('apr-util',builddir.meta['PKG']):
      builddir.env['CC']="gcc -std=gnu99"
      builddir.conf_test.append("--with-apr=/usr --with-openssl=/usr --with-sqlite3=/usr --with-expat=/usr --with-berkeley-db=/usr")
      builddir.conf_test.append("--with-crypto --with-ldap")

    if re.match('autogen',builddir.meta['PKG']):
      builddir.root_redir=[]

    if re.match('avahi',builddir.meta['PKG']):
      builddir.conf_test.append("--with-distro=gentoo --enable-core-docs --enable-compat-libdns_sd --enable-compat-howl")
      builddir.conf_test.append("--disable-mono --disable-gtk3")
      # XXX
      builddir.conf_test.append("--disable-pygtk --disable-python-dbus --disable-qt3 --disable-qt4")
      builddir.conf_test.append("--with-autoipd-user=autoipd --with-autoipd-group=autoupd")

    if re.match('pulseaudio',builddir.meta['PKG']):
      builddir.conf_test.append("--with-access-group=pulseacc --enable-lirc --enable-udev --with-fftw --disable-tcpwrap")

    if re.match('bash',builddir.meta['PKG']):
      ## flavour minimal vs none
      builddir.conf_test.append("--with-installed-readline --with-curses")

    if re.match('binutils',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-targets=i586-pc-linux-gnu,i586-pc-mingw32,x86_64-pc-linux-gnu,x86_64-pc-mingw32,i386-linux-uclibc,arm-linux-gnueabi,mipsel-linux-uclibc,m68k-linux-gnu")
#     builddir.conf_test.append("--enable-gold") -- gold is not compatible with most unusual platforms yet
      builddir.conf_files.append("bfd/configure")
      builddir.use_dir('BUILD')
      builddir.conf_test.append("--build=%s --host=%s"%(BUILD,BUILD,))
#     builddir.conf_test.append("--host=x86_64-pc-linux-gnu --build=i586-pc-linux-gnu")

    if builddir.meta['PKG'] == 'cairo':
      builddir.conf_test.append("--enable-gl --enable-drm --enable-xlib-xcb")

    if re.match('cloog',builddir.meta['PKG']):
      builddir.conf_test.append("--with-isl=system")

    if re.match('collectd',builddir.meta['PKG']):
      builddir.env['ac_cv_lib_iptc_iptc_init']='yes'
      builddir.env['ac_cv_type_iptc_handle']='yes'
      builddir.env['ac_cv_type_ip6tc_handle']='yes'
      #builddir.conf_test.append("--disable-iptables")
      builddir.env['CONFIG_SHELL']='/bin/bash'
      builddir.conf_test.append("--enable-nut")

    if re.match('cups',builddir.meta['PKG']):
      builddir.conf_test.append("--with-cups-user=cups --with-cups-group=cups --disable-pam --disable-slp")
      builddir.make_files.append('Makedefs')
      builddir.install_test.append("BUILDROOT=$ROOT")

    if re.match('db',builddir.meta['PKG']):
      builddir.use_dir('BUILD')
      builddir.conf_test.append("--enable-tcl --enable-cxx --enable-compat185 --enable-java --with-tcl=/usr/lib")
      builddir.install_test.append("docdir=/usr/share/doc/db")

    if re.match('dhcp',builddir.meta['PKG']):
      builddir.conf_test.append("--with-srv-lease-file=/var/lib/dhcp/dhcpd.leases")
      builddir.conf_test.append("--with-cli-lease-file=/var/lib/dhcp/dhclient.leases")
      builddir.conf_test.append("--with-srv6-lease-file=/var/lib/dhcp/dhcpd6.leases")
      builddir.conf_test.append("--with-cli6-lease-file=/var/lib/dhcp/dhclient6.leases")
      builddir.env['CFLAGS']=builddir.cflags(opt="-Os")
      builddir.make_test.append("DEBUG='-Os -DNOMINUM' VARDB=/var/lib/dhcp")
#        perl -pi -e 's,/var/state/dhcp,/var/lib/dhcp,g' includes/cf/linux.h
#        make DEBUG='-Os -DNOMINUM' VARDB=/var/lib/dhcp


    if re.match('djvulibre',builddir.meta['PKG']):
      builddir.conf_test.append("--with-qt --enable-threads --enable-djview")

    if builddir.meta['PKG'] == 'doxygen':
      builddir.env['CFLAGS']=builddir.cflags(exc='-fno-exceptions -fno-rtti')
      builddir.env['CXXFLAGS']=builddir.cflags(exc='-fno-exceptions -fno-rtti')
      builddir.conf_add.append("--prefix /usr --docdir /usr/share/doc")
      builddir.make_files.append("src/Makefile.libdoxycfg")
      builddir.make_test.append("CFLAGS=$CFLAGS CXXFLAGS=$CXXFLAGS")
      builddir.install_test.append("!INSTALL=/usr")

    if re.match('e2fsprogs',builddir.meta['PKG']):
      builddir.env['DEVMAPPER_LIBS']='-ldevmapper  -lpthread'
      builddir.env['STATIC_DEVMAPPER_LIBS']='-ldevmapper  -lpthread'
      builddir.env['LDFLAG_STATIC']=''
      builddir.conf_test.append("--enable-dynamic-e2fsck --enable-fsck --enable-blkid-devmapper --enable-elf-shlibs")
      builddir.conf_test.append("--disable-libblkid --disable-libuuid --disable-uuidd")
      builddir.install_test.append("install-libs")

    if re.match('esound',builddir.meta['PKG']):
      builddir.env['CFLAGS']=builddir.cflags(f64='')

    if re.match('faac',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-drm --with-mp4v2")

    if re.match('faad2',builddir.meta['PKG']):
      builddir.conf_test.append("--with-drm --with-mpeg4ip")

    if re.match('fakeroot',builddir.meta['PKG']):
      builddir.env['CFLAGS']=builddir.cflags(f64='')
      builddir.conf_files.append("configure.sh")

    if re.match('ffmpeg',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-version3 --enable-gpl --enable-nonfree --enable-swscale --enable-postproc --disable-debug")
      builddir.conf_test.append("--enable-libfaac --enable-libmp3lame --enable-libspeex --enable-libvorbis --enable-libcelt")
      builddir.conf_test.append("--enable-libx264 --enable-libvpx --enable-libtheora --enable-libschroedinger")
      builddir.conf_test.append("--enable-libdirac --enable-libxvid --enable-libvo-aacenc")

    if re.match('file',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-fsect-man5")
      builddir.make_test.append("pkgdatadir=/etc")
      builddir.install_test.append("pkgdatadir=/etc")

    if re.match('freetype',builddir.meta['PKG']):
      builddir.conf_files.append("builds/unix/configure")
      builddir.make_files.append("builds/unix/install.mk")

    if re.match('gamin',builddir.meta['PKG']):
      builddir.env['CFLAGS']=builddir.cflags(exc='-fexceptions')+" -DG_CONST_RETURN=const"
      builddir.conf_test.append("--libexecdir=/usr/sbin")

    if re.match('gettext',builddir.meta['PKG']):
      builddir.conf_test.append("--without-emacs")

    if re.match('glibc',builddir.meta['PKG']):
      builddir.env['CFLAGS']='-Os'
      builddir.env['CXXFLAGS']='-Os'
      builddir.env['LDFLAGS']='-s'
      builddir.use_dir('BUILD')
      builddir.conf_test.append("--libexecdir=/usr/lib/misc --localstatedir=/var --mandir=/usr/share/man --infodir=/usr/share/info")
      builddir.conf_test.append("--enable-add-ons=libidn,nptl --enable-bind-now --enable-kernel=2.6.26 --disable-profile")
      builddir.conf_test.append("--with-gd=no --without-cvs")
      builddir.install_test.append("install_root=$ROOT")
      builddir.root_redir=[]
      #builddir.conf_add.append("i586-pc-linux-gnu")
      # cross
      #uilddir.env['CC']='x86_64-pc-linux-gnu-gcc -m64'
      if False:
        builddir.env['CC']='x86_64-pc-linux-gnu-gcc -m32' #-m64
        builddir.conf_test.append("--build=i586-pc-linux-gnu --host=x86_64-pc-linux-gnu")
        builddir.conf_test.append("--prefix=/usr/x86_64-pc-linux-gnu")
        # 64: lib64|lib +lib32 +libx32
        # 32: lib
        builddir.conf_test.append("--libdir=/usr/x86_64-pc-linux-gnu/lib32 --libexecdir=/usr/x86_64-pc-linux-gnu/lib32")
        builddir.conf_test.append("--sysconfdir=/usr/x86_64-pc-linux-gnu/etc")
        builddir.conf_test.append("!--localstatedir= !--mandir= !--infodir=")

    if re.match('gcc',builddir.meta['PKG']):
      builddir.conf_files.append("gcc/configure libjava/configure")
      builddir.conf_test.append("--with-system-zlib --enable-threads")
      builddir.conf_test.append("--enable-languages=c,c++,go,objc,java,ada,fortran")
      builddir.conf_test.append("--enable-cloog-backend=isl")
      builddir.conf_add.append("--with-ecj-jar=/usr/share/java/ecj.jar")
      builddir.conf_add.append("--enable-__cxa_atexit --enable-clocale=gnu --enable-libada")
      builddir.use_dir('BUILD')
      ## todo
      #uilddir.conf_add.append("i586-pc-linux-gnu")
      #uilddir.conf_test.append("--host=i586-pc-linux-gnu --build=i586-pc-linux-gnu --target=x86_64-pc-mingw32")
      builddir.conf_test.append("--host=i586-pc-linux-gnu --build=i586-pc-linux-gnu --target=x86_64-pc-linux-gnu")
      builddir.conf_add.append("--enable-multiarch --with-abi=m64 --with-multilib-list=m64,mx32 --with-tune=generic")
      #pass1
      #builddir.conf_test.append("--enable-languages=c,c++")
      #builddir.conf_test.append("--with-newlib --without-headers")
      #builddir.conf_add.append("--disable-decimal-float --disable-threads --disable-libatomic --disable-libgomp --disable-libitm --disable-libmudflap --disable-libquadmath --disable-libsanitizer --disable-libssp")
      #builddir.conf_add.append("--disable-libstdc++-v3")
      # with-arch --with-tune --with-abi --with-float=soft/hard
      # --build=x86_64-linux-gnu --host=x86_64-linux-gnu --target=x86_64-linux-gnu
      # raspberry
      # --with-arch=armv6 --with-tune=arm1176jz-s --with-fpu=vfp
      # beaglebone
      # armv7a-hardfloat-linux-gnueabi

    if re.match('gmp',builddir.meta['PKG']):
      builddir.env['CFLAGS']=builddir.cflags(exc='-fexceptions')
      builddir.env['CXXFLAGS']=builddir.cflags(exc='-fexceptions')
      builddir.conf_test.append("--enable-cxx --enable-mpfr --enable-mpbsd")
      ## flavour i386 vs i686
      builddir.conf_test.append("--build=i386-pc-linux-gnu")

    if re.match('gnome-settings-daemon|gnome-keyring',builddir.meta['PKG']):
      builddir.conf_test.append("--x-libraries=/usr/X11R6/lib --libexecdir=/usr/bin")

    if re.match('gnome-vfs|libgnome|libsoup',builddir.meta['PKG']):
      builddir.env['CFLAGS']=builddir.cflags()+' -UG_DISABLE_DEPRECATED';
      builddir.env['PATH']='/bin:/usr/bin'
      builddir.conf_test.append("--enable-cdda")

    if re.match('gnupg',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-gpgtar --libexecdir=/usr/lib/gnupg")

    if re.match('gnutls',builddir.meta['PKG']):
      builddir.conf_test.append("--with-lzo")

    if re.match('groff',builddir.meta['PKG']):
      builddir.conf_test.append("--with-appresdir=/etc/X11/app-defaults")

    if re.match('guile',builddir.meta['PKG']):
      builddir.env['CFLAGS']=builddir.cflags(opt='-O2',fp='',exc='')

    if re.match('gupnp',builddir.meta['PKG']):
      #   --enable-introspection=[no/auto/yes]
      builddir.conf_test.append("--enable-introspection=no")

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

    if re.match('iptables',builddir.meta['PKG']):
      builddir.conf_test.append("--exec-prefix= --sbindir=/sbin")

    if re.match('libbonobo',builddir.meta['PKG']):
      # DEPRECATED
      builddir.conf_test.append("--libexecdir=/usr/bin")

    if re.match('libdv',builddir.meta['PKG']):
      builddir.conf_test.append("--disable-xv")

    if re.match('libquicktime',builddir.meta['PKG']):
      builddir.conf_test.append("--with-libdv --enable-gpl --with-faac --with-faad2")
      # make + make install in utils
      # patch png12/png14

    if re.match('libvpx',builddir.meta['PKG']):
      builddir.conf_add.append("--prefix=/usr")

    if re.match('libxml2',builddir.meta['PKG']):
      builddir.conf_test.append("--with-icu")

    # ldns - config/make/install in examples&drill -- flavour?

    if re.match('Linux-PAM',builddir.meta['PKG']):
      builddir.conf_test.append("--libdir=/lib")

    if re.match('LVM2',builddir.meta['PKG']):
      builddir.conf_test.append("--sbindir=/sbin --libdir=/lib --exec-prefix= --enable-static_link")
      builddir.make_files.append('make.tmpl')

    if re.match('lzip',builddir.meta['PKG']):
      builddir.conf_test.append("CXXFLAGS=$CXXFLAGS")
      builddir.conf_test.append("LDFLAGS=$LDFLAGS")

    if re.match('MesaLib',builddir.meta['PKG']):
      # glu in freeglu
      builddir.conf_test.append("--enable-gles1 --enable-gles2 --enable-osmesa")
      builddir.conf_test.append("--with-gallium-drivers=i915,ilo,nouveau,r300,swrast")
      #uilddir.conf_test.append("--with-gallium-drivers=i915,ilo,nouveau,r300,r600,radeonsi,freedreno,svga,swrast")

    if re.match('mkvtoolnix',builddir.meta['PKG']):
      builddir.env['SHELL']='/bin/bash'
      # rake;rake install prefix=`pwd`/ROOT/usr

    if re.match('mpfr',builddir.meta['PKG']):
      builddir.env['CFLAGS']=builddir.cflags(exc='-fexceptions')
      builddir.env['CXXFLAGS']=builddir.cflags(exc='-fexceptions')
      builddir.conf_test.append("--build=i386-pc-linux-gnu")

    if re.match('mysql',builddir.meta['PKG']):
      builddir.conf_test.append("--with-mysqld-user=mysql --emable-thread-safe-client")
      builddir.conf_test.append("--without-bench --with-extra-charsets=complex")
      builddir.conf_test.append("--localstatedir=/var/lib/mysql --libexecdir=/usr/sbin")

    if re.match('neon',builddir.meta['PKG']):
      builddir.conf_test.append("--with-ssl=openssl")

    if re.match('net-snmp',builddir.meta['PKG']):
      builddir.conf_test.append("--with-sys-contact=snmp --with-sys-location=Unknown --with-logfile=none")
      builddir.conf_test.append("--with-persistent-directory=/var/lib/snmp --with-default-snmp-version=2")
      builddir.conf_test.append("--without-python-modules --without-perl-modules")
      builddir.install_test.append('!INSTALL=')

    if re.match('nginx',builddir.meta['PKG']):
      builddir.conf_files.append("auto/options")
      builddir.conf_test.append("--prefix=/usr --pid-path=/var/run/nginx.pid")
      builddir.conf_test.append("--error-log-path=/var/log/nginx/error.log --http-log-path=/var/log/nginx/access.log")
      builddir.conf_test.append("--conf-path=/etc/nginx/nginx.conf --lock-path=/var/run/nginx.lock")
      builddir.conf_test.append("--http-client-body-temp-path=/var/cache/nginx/client_body --http-proxy-temp-path=/var/cache/nginx/proxy")
      builddir.conf_test.append("--http-fastcgi-temp-path=/var/cache/nginx/fastcgi --http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp")
      builddir.conf_test.append("--http-scgi-temp-path=/var/cache/nginx/scgi_temp")
      # essential
      builddir.conf_test.append("--with-http_ssl_module --with-http_v2_module")
      # useful
      builddir.conf_test.append("--with-http_stub_status_module --with-http_realip_module")
      # extra tools
      builddir.conf_test.append("--with-http_sub_module --with-http_addition_module")
      builddir.conf_test.append("--with-http_gzip_static_module --with-http_random_index_module")
      builddir.conf_test.append("--with-http_degradation_module --with-http_secure_link_module")
      # --with-http_stub_status_module --with-http_random_index_module")

    if re.match('nilfs-utils',builddir.meta['PKG']):
      builddir.conf_test.append("--without-selinux")

    if re.match('node',builddir.meta['PKG']):
      builddir.env['SHELL']='python'

    if re.match('nut',builddir.meta['PKG']):
      builddir.conf_test.append("--datarootdir=/usr/share/nut --sysconfdir=/etc/nut --mandir=/usr/share/man --with-dev --wixh-doc")
      builddir.conf_test.append("--with-statepath=/var/lib/ups --with-ssl --with-user=ups --with-group=ups")

    if re.match('ntp',builddir.meta['PKG']):
      builddir.conf_test.append("--disable-all-clocks")
      builddir.conf_test.append("--enable-RAWDCF --enable-LOCAL-CLOCK --enable-DUMBCLOCK --enable-NMEA")
      builddir.conf_test.append("--enable-ARCRON-MSF")
      builddir.conf_test.append("--enable-linuxcaps --enable-ipv6 --enable-tickadj=120")

    if re.match('ocaml',builddir.meta['PKG']):
      builddir.conf_add.append("--prefix /usr")
      builddir.make_files.append("config/Makefile")
      builddir.make_test=["world opt opt.opt"]
      builddir.install_test.append("PREFIX=$ROOT/usr")
      builddir.root_redir=[]

    if re.match('openldap',builddir.meta['PKG']):
      builddir.conf_test.append("--libexecdir=/usr/sbin --localstatedir=/var/lib/openldap-data")
      builddir.conf_test.append("--enable-ipv6 --enable-rewrite --enable-bdb --enable-hdb --enable-meta --enable-ldap --enable-overlays")
      builddir.conf_test.append("--without-cyrus-sasl --disable-spasswd --disable-perl")
      builddir.make_test = ["depend all"]

    if builddir.meta['PKG'] == 'p11-kit':
      builddir.conf_test.append("--without-trust-paths")

    if re.match('pinentry',builddir.meta['PKG']):
      builddir.conf_test.append("--disable-pinentry-qt4")

    if re.match('pcre',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-utf8 --enable-unicode-properties --enable-pcre16 --enable-jit")
      builddir.conf_test.append("--enable-pcregrep-libz --enable-pcregrep-libbz2")

    if re.match('pcsc-lite',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-usbdropdir=/usr/lib/pcsc/drivers --enable-muscledropdir=/usr/lib/pcsc/services")
      builddir.conf_test.append("--enable-extendedapdu --enable-debugatr")

    if re.match('poppler',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-zlib --enable-gtk-doc --enable-xpdf-headers")

    if re.match('qemu',builddir.meta['PKG']):
      builddir.env['CFLAGS']=builddir.cflags(exc='')+' -I/usr/X11/include'
      builddir.env['LDFLAGS']=builddir.ldflags()+' -L/usr/X11/lib'

    if re.match('ruby',builddir.meta['PKG']):
      builddir.make_files.append("common.mk")

    if re.match('rsync',builddir.meta['PKG']):
      builddir.conf_files.append("configure.sh")
      builddir.conf_test.append("--with-rsh=ssh --enable-acl-support")

    if builddir.meta['PKG'] == 'rrdtool':
      builddir.conf_test.append("--disable-perl --disable-lua")

    if re.match('subversion',builddir.meta['PKG']):
      builddir.env['CC']="gcc -std=gnu99"
      builddir.install_test.append("install-swig-rb install-swig-py install-swig-pl")

    if re.match('tar',builddir.meta['PKG']):
      builddir.env['tar_cv_path_RSH']='/usr/bin/ssh'
      builddir.conf_test.append("--libexecdir=/etc")

    if re.match('tcl|tk',builddir.meta['PKG']):
      builddir.use_dir('BUILD')
      builddir.conf_test.append("--without-tzdata")
      builddir.install_test.append("install-private-headers")

    if re.match('util-linux',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-arch --enable-kill --enable-raw --enable-rdev --enable-write --disable-mountpoint")

    if re.match('vim',builddir.meta['PKG']):
      builddir.conf_test.append("--disable-selinux --enable-pythoninterp --enable-cscope --enable-multibyte --enable-gui=gtk2")
      builddir.conf_files.append("src/auto/configure")
      ## flavour nogui (vs gtk2)
#     builddir.conf_test.append("--disable-gui --without-x --disable-xim")

    if re.match('webkit',builddir.meta['PKG']):
      builddir.env['SHELL']='/bin/bash'
      builddir.conf_test.append("--enable-geolocation --enable-web-sockets")

    if re.match('wget',builddir.meta['PKG']):
      #builddir.env['ac_cv_gnutls']='no'
      builddir.conf_test.append("--with-openssl=yes --with-ssl=openssl")

    if re.match('wxWidgets|wxPython',builddir.meta['PKG']):
      # wxpython actually lives in a subdirectory - flavour?
      builddir.conf_test.append("--disable-compat26 --with-opengl --enable-unicode")

    if re.match('x264',builddir.meta['PKG']):
      builddir.env['SHELL']='/bin/bash'
      builddir.make_files.append('config.mak')

    if re.match('xvidcore',builddir.meta['PKG']):
      builddir.use_dir("build/generic")

    if re.match('zlib',builddir.meta['PKG']):
      builddir.conf_test.append("--prefix=/usr")

    if re.match('zsh',builddir.meta['PKG']):
      builddir.conf_test.append("--enable-maildir-support --with-curses-terminfo --disable-gdbm --enable-pcre")

    env=[]
    for v in sorted(builddir.env.iterkeys()):
      env.append("%s=%s"%(v,builddir.env[v]))

    cmdline=['$SHELL',builddir.rel_to_use(self.conf_script)]
    cmdline.extend(shlex.split(" ".join(builddir.conf_add)))
    possible_opts=shlex.split(" ".join(builddir.conf_test))
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
    self.root_redir=["cxroot","$ROOT"]
    self.env={}
    self.env['CC']="gcc"
    self.env['CXX']="g++"
    self.env['SHELL']='/bin/sh'
    self.env['CFLAGS']=self.cflags()
    self.env['CXXFLAGS']=self.cflags(exc='')
    self.env['LDFLAGS']=self.ldflags()
    self.mustsucceed=True

    self.conf_files=[]
    # or perhaps use make -p
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

    # Some packages using cmake and configure use cmake for other platforms
    # and less Unixy features - no symbol versioning, no tools, no .la files.
    # fMake the exceptions here
    if self.check_file('configure') and self.meta['PKG'] not in ['llvm','cfe','cmake']:
      self.pkg = AutoconfPackage('./configure')
    # cmake
    elif self.check_file('bootstrap'):
      self.pkg = AutoconfPackage('./bootstrap')
    # Berkeley db
    elif self.check_file('dist/configure'):
      self.pkg = AutoconfPackage('dist/configure')
    # tcl/tk
    elif self.check_file('unix/configure'):
      self.pkg = AutoconfPackage('unix/configure')
    # ICU4C
    elif self.check_file('source/configure'):
      self.pkg = AutoconfPackage('source/configure')
    elif self.check_file('build/generic/configure'):
      self.pkg = AutoconfPackage('build/generic/configure')
    elif self.check_file('setup.py'):
      self.pkg = PythonPackage('setup.py')
    elif self.check_file('Jamroot'):
      self.pkg = JamPackage('Jamroot')
    elif self.check_file('CMakeLists.txt'):
      self.pkg = CmakePackage("CMakeListst.txt")
    elif self.check_file('SConstruct'):
      self.pkg = SconsPackage('SConstruct')
    else:
      self.pkg = Package("Unknown",None)

    os.chdir(self.nn_root)
    self.cwd = self.nn_root

  def ldflags(self):
    return "-s -Wl,--as-needed"

  def cflags(self,opt='-Os',debug='',exc='-fno-asynchronous-unwind-tables',fp='-fomit-frame-pointer',f64='-D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64'):
    a=[x for x in [opt,debug,exc,fp,f64] if x]
    return " ".join(a)
    # -O2 -Os None
    # -g None
    # -fno-asynchronous-unwind-tables -fno-exceptions -fexceptions
    # -fomit-frame-pointer None

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
      npath = os.path.relpath(path,os.path.join(self.nn_root,self.cwd_use))
    else:
      npath = os.path.relpath(path,os.path.join(self.nn_root,self.cwd))

    if npath == 'configure': return "./configure"
    return npath

  def set_debug(self,debug):
    self.debug=debug

  def command(self,cmd,vars=None,logto=None):
    os.chdir(self.nn_root)
    if logto:
      logdir = os.path.join('.nnpkg',logto)
      done = os.path.exists("%s/donestate"%(logdir,))
    else:
      logdir=None
      done=False

    if self.do_multilog and logto and not self.debug and not done:
      try: os.mkdir(logdir)
      except: pass
      log_proc = subprocess.Popen(['multilog','t','s999999','n25',logdir],stdin=subprocess.PIPE)
    else: log_proc = None

    if done:
      print "# not running %s again"%(logto,)

    if vars and len(vars)>0:
      for v in vars:
        (name,line)=v.split("=",1)
        if name not in self.exec_env or line != self.exec_env[name]:
          l = os.path.expandvars(line)
          self.exec_env[name]=l
          os.environ[name]=l
          if log_proc: log_proc.stdin.write("! export %s\n"%(v,))
          print "! export",v

    for name in self.env:
      if name not in self.exec_env:
        l = os.path.expandvars(self.env[name])
        self.exec_env[name]=l
        os.environ[name]=l
        if log_proc: log_proc.stdin.write("! export %s=%s\n"%(name,l,))
        print "! export %s=%s"%(name,l,)

    if done:
      return 0

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
    if cmd_proc.returncode!=0 and self.mustsucceed:
      print "command exited with %d"%(cmd_proc.returncode,)
      sys.exit(1)

    os.chdir(self.nn_root)

    if logdir:
      with open("%s/donestate"%(logdir,),'a'):
        pass

    return 0

  def setup(self):
    self.pkg.setup(self);

  def build(self):
    self.pkg.build(self);

  def install(self):
    self.pkg.install(self);
    # done, go back to root to not surprise anything running after us
    self.use_dir(self.nn_root)
