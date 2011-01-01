#!/usr/bin/python
# miv: ts=8 sw=4 sta sts=4 ai

import os
import re
import string

from pysqlite2 import dbapi2 as db

SRCDIR='/usr/src'
DBFILE=None

def whurl(db_conn,filename):
	import pkgname

	(dir,fn)=os.path.split(filename)
	#{'pre': '-', 'ext': '.tar.bz2', 'tag': '', 'ver': '0.8.0', 'pkg': 'libebml'}
	tofind = pkgname.pkgsplitname(fn)

	cur = db_conn.cursor()
	url = None

	cur.execute("select path,fn,url from meta where fn like ? order by stamp desc",(tofind['pkg']+"%",))
	for row in cur.fetchall():
		(oldpath,oldfn,oldurl)=row
		oldpkg = pkgname.pkgsplitname(oldfn)
		if oldpkg['pkg'] == tofind['pkg']:
			# XXX oldpkg ext starts with tofind ext
			if oldpkg['pre']==tofind['pre'] and \
			   tofind['ext'] in oldpkg['ext'] and \
			   oldpkg['tag']==tofind['tag'] and oldfn != fn:
				possibleurl = re.sub(oldfn,fn,oldurl)
				possibleurl = re.sub(oldpkg['ver'],tofind['ver'],possibleurl)
				#XXX uniquify
				print possibleurl
	cur.close()

	return

#    cur = db_conn.cursor();
#    if re.search('^[0-9a-fA-F]{%d,}$'%(try_hash_min,),arg):
#	cur.execute("select path,fn,md5,sha1,sha256,url from meta where md5||':'||sha1||':'||sha256 like ? order by stamp desc limit ?",('%'+arg+'%',max_rows,))

def main(db_conn,argv=[]):
	for l in argv:
		whurl(db_conn,l)

if __name__ == '__main__':
        import sys
	
	DBFILE = os.environ['FLDB']

	with db.connect(DBFILE) as db_conn:
        	sys.exit(main(db_conn,sys.argv[1:]))

