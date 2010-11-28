#!/usr/bin/python
# miv: ts=8 sw=4 sta sts=4 ai

import os
import re

from pysqlite2 import dbapi2 as db

SRCDIR='/usr/src'
DBFILE=None

def zxvf(db_conn,filename):
	import pkgname

	(dir,fn)=os.path.split(filename)
	#{'pre': '-', 'ext': '.tar.bz2', 'tag': '', 'ver': '0.8.0', 'pkg': 'libebml'}
	prop = pkgname.pkgsplitname(fn)

	cur = db_conn.cursor()

	cur.execute("select path,fn,url from meta where fn=? order by stamp desc limit 1",(fn,))
	for row in cur.fetchall():
		newfn = os.path.join(row[0],row[1])
		if filename != newfn:
			filename = newfn

	cur.execute("select path,fn from meta where fn like ? order by stamp desc",(prop['pkg']+"%",))
	for row in cur.fetchall():
		(candidatepath,candidatefn)=row
		candidate = pkgname.pkgsplitname(candidatefn)
		if candidate['pkg'] == prop['pkg'] and candidate['ver'] == prop['ver']:
			if (candidatefn != fn):
				print "similar",candidate,fn,candidatefn
	cur.close()

	print "not unpacking", filename, prop
	return

#    cur = db_conn.cursor();
#    if re.search('^[0-9a-fA-F]{%d,}$'%(try_hash_min,),arg):
#	cur.execute("select path,fn,md5,sha1,sha256,url from meta where md5||':'||sha1||':'||sha256 like ? order by stamp desc limit ?",('%'+arg+'%',max_rows,))

def main(db_conn,argv=[]):
	pwd = os.getcwd()
	if None and not re.search('^'+SRCDIR+'($|/)',pwd):
		raise ValueError
	
	for l in argv:
		zxvf(db_conn,l)

if __name__ == '__main__':
        import sys
	
	DBFILE = os.environ['FLDB']

	with db.connect(DBFILE) as db_conn:
        	sys.exit(main(db_conn,sys.argv[1:]))

