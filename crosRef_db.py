#!/usr/bin/env python
DEFINED = 1
USED = 2
MACRO = 4

import os
import sys
import MySQLdb as DB
verbose = 0
reference ={}
import myutils
	
def put_in_file(txt,fd,defined_symbols):
	"""
	# write the internal structure to a file
	# sort the keys (names) and files
	"""

	if len(txt) > 0: fd.write(txt+'\n')
	referenceKeys = sorted(defined_symbols.iterkeys())
	for i in referenceKeys:
		dict_of_files = defined_symbols[i]						# dict of files:list of tuples
		try:
			fd.write('name='+i+'\n')
			if len(dict_of_files) > 0:
				list_of_files = sorted(dict_of_files.iterkeys()) 	# list of tuples (file , list of tuples)
				for	j in list_of_files:
					fd.write('file='+j+'\n')    
					for k in dict_of_files[j]:
						if k[1] == DEFINED:
							tp = "defin"
						elif k[1] == USED:
							tp = "refer"
						elif k[1] == MACRO:
							tp = "macro"
						else:
							tp = "both "
						s = str(k[0])
						for p in k[2]:
							s += ':'+str(p)
						fd.write(' line='+s+' type='+tp)	# line ond type
					fd.write('\n')
		except :
			print "ERR - " + i
			print dict_of_files

def createDataBase(mysql,dbase):
	"""
	delete the previous data base with the given name, if any
	create a cross reference data base
	"""
	sql = 'CREATE DATABASE IF NOT EXISTS '+ dbase + ';'
	mysql.query(sql)
	mysql.select_db(dbase)
	sql = 'DROP TABLE IF EXISTS names;'
	mysql.query(sql)
	sql = 'DROP TABLE IF EXISTS files;'
	mysql.query(sql)
	sql = 'DROP TABLE IF EXISTS linesinfile;'
	mysql.query(sql)
	sql = 'DROP TABLE IF EXISTS allfiles;'
	mysql.query(sql)
	sql = 'DROP TABLE IF EXISTS allnames;'
	mysql.query(sql)
	sql = 'CREATE TABLE names (id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
	name TINYTEXT NOT NULL);'
	mysql.query(sql)
	sql = 'CREATE TABLE files (id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
		name BIGINT NOT NULL, \
		filename TEXT NOT NULL \
		REFERENCES names(id));'
	mysql.query(sql)
	sql = 'CREATE TABLE linesinfile (id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
		filename BIGINT NOT NULL, \
		number TEXT NOT NULL, \
		ref TINYTEXT NOT NULL \
		REFERENCES files(id));'
	mysql.query(sql)   
	sql = 'CREATE TABLE allfiles (id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
	file TEXT NOT NULL);'
	mysql.query(sql)
	sql = 'CREATE TABLE allnames (id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
		file BIGINT NOT NULL, \
		name TEXT NOT NULL \
		REFERENCES allfiles(id));'
	mysql.query(sql)

def insertValues(defined_symbols,mysql,list_of_files,last_name,name,newfile,rowd):
	"""
	Insert files and lines into data base
	"""

	crs = mysql.cursor()
	for j in list_of_files:
		fn = j.replace(os.sep,'=')
		if newfile and rowd != None:
			if fn in rowd:
				continue    
		try:				
			ltp = defined_symbols[name][j] # list of tuples (line number reference)
			sql1 = '"%d", "%s"' % (last_name,fn)
			sql = 'INSERT INTO files (name,filename) VALUES ('+sql1+');'
			crs.execute(sql)
			last_file = crs.lastrowid
			for k in ltp:
				if k[1] == DEFINED:
					tp = "defin"
				elif k[1] == USED:
					tp = "refer"
				elif k[1] == MACRO:
					tp = "macro"
				else:
					tp = "both "
			s = str(k[0])
			sql1 = '"%d", %s, "%s"' % (last_file,s,tp)
			sql = 'INSERT INTO linesinfile (filename,number,ref) VALUES ('+sql1+');'
			crs.execute(sql)
		except TypeError as e:
			print "ERROR ("+str(e)
			print name + " , "+ j 
			print ltp
			sys.exit()
		except mysql.Error as err:
			print 'ERROR DataBase '+str(err)
			mysql.rollback() 
	mysql.commit()
	crs.close()

def buildallfiles(defined_symbols):
	allfiles = {}
	for name in defined_symbols.keys():
		files = defined_symbols[name]
		for filename in files.keys():
			if filename in allfiles.keys() and not name in allfiles[filename]: 
				allfiles[filename].append(name)
			else:
				allfiles[filename]=[name]
	return allfiles

def put_in_db(dbase,defined_symbols,createDB):
	"""
	open a mySQL connection; select the given data base
	run along defined symbols and insert into data base
	"""
	
	mysql = DB.connect(host="127.0.0.1",user=myutils.mysqluser,passwd=myutils.mysqlpwd) 
	if createDB:
	    createDataBase(mysql,dbase)
	try:
	    mysql.select_db(dbase)
	except : 
	    print 'DataBase '+dbase+ ' does not exist'
	    return
	referenceKeys = sorted(defined_symbols.iterkeys())

	cr = mysql.cursor()
	try:
		if createDB:
			for i in referenceKeys:
				dict_of_files = defined_symbols[i]						# dict of files:list of tuples
				if len(dict_of_files) > 0:
					list_of_files = sorted(dict_of_files.iterkeys()) 	# list of tuples (file , list of tuples)
					sql1 = '"%s"' % (i)
					sql = "INSERT INTO names (name) VALUES ("+sql1+");"
					cr.execute(sql)
					mysql.commit()
					last_name = cr.lastrowid
					insertValues(defined_symbols,mysql,list_of_files,last_name,i,False,0)
			allfilesd = buildallfiles(defined_symbols)
			crs = mysql.cursor()
			for j in allfilesd.keys():
				fn = j.replace(os.sep,'=')
				sql1 = '"%s"' % (fn)
				sql = "INSERT INTO allfiles (file) VALUES ("+sql1+");"
				cr.execute(sql)
				mysql.commit()
				last_file = cr.lastrowid
				for n in allfilesd[j]:
					sql1 = '"%d", "%s"' % (last_file,n)
					sql = 'INSERT INTO allnames (file,name) VALUES ('+sql1+');'
					crs.execute(sql)
			mysql.commit()
			crs.close()
		else:
			for i in referenceKeys:
				sql2 = ''
				dict_of_files = defined_symbols[i]					# dict of files:list of tuples
				list_of_files = sorted(dict_of_files.iterkeys()) 	# list of tuples (file , list of tuples)
				sql1= '"%s"' % (i)
				sql = "SELECT * FROM names WHERE name="+ sql1+";"
				cr.execute(sql)
				mysql.commit()
				row = cr.fetchone()
				if row != None:
					sql2 = '"%d"' % (row[0])
					sql = 'SELECT * FROM files WHERE  name='+ sql2+";"
					cr.execute(sql)
					rowd = cr.fetchall()
					insertValues(defined_symbols,mysql,list_of_files,row[0],i,True,rowd)
				else:
					sql = "INSERT INTO names (name) VALUES ("+sql1+");"
					cr.execute(sql)
					mysql.commit()
					last_name = cr.lastrowid
					insertValues(defined_symbols,mysql,list_of_files,last_name,i,False,0)

	except mysql.Error as err:
		print 'ERROR DataBase '+str(err)
		mysql.rollback() 
		return

	cr.close()
	mysql.close()

def ProcessEntryFile(fd):
	"""
	parse a ref file and build a defined symbols dict
	"""
	global reference

	name = ''
	filename = ''
	dd = {}
	eof = False
	while not eof:
		line = fd.readline()
		if len(line) == 0:
			eof = True
			if name in reference.keys():
				reference[name] = dd
			elif name != '':
				reference[name] = dd
			#if verbose: print reference
		else:
			line = line.strip()
			if line.startswith('name'):
				if name in reference.keys() or name != '':
					reference[name] = dd
				tokens = line.split()
				nn = tokens[0].split('=')
				name = nn[1]
				dd = {}
			elif line.startswith('file'):
				filename = line[len('file='):]
				if name in reference.keys():
					dd 	= reference[name]
					if dd.has_key(filename):
						filename = ''
			else:
				if filename != '':
					tokens = line.split()
					length = len(tokens)
					#print tokens
					first = True
					for t in range(0,length,2):
						pos = tokens[t].find('=')
						countline = int(tokens[t][pos+1:])
						pos = tokens[t+1].find('=')
						ref = tokens[t+1][pos+1:]
						tline = (countline,ref)
						if first:
							dd[filename] = [tline]
							first = False
						else:
							ff = dd[filename] #list of tuples (line,ref)				
							ff.append(tline)
							dd[filename] = ff

def ProcessEntryBase(fd):
	"""
	parse a pyt data base and build a defined symbols dict
	"""
	global reference

	name = ''
	filename = ''
	dd = {}

	mysql = DB.connect(host="127.0.0.1",user=myutils.mysqluser,passwd=myutils.mysqlpwd) 
	try:
	    mysql.select_db(fd)
	except : 
	    print 'DataBase '+fd+ ' does not exist'
	    return
	sql = "SELECT * FROM names;"
	mysql.query(sql)
	r = mysql.store_result()
	row = r.fetch_row(0)
	for rr in row:
		last_name = rr[0]
		sql2 = '"%s"' % (last_name)
		sql = 'SELECT * FROM files WHERE  name='+ sql2+";"
		mysql.query(sql)
		rf = mysql.store_result()
		rowd = rf.fetch_row(0)
		dd = {}
		name = rr[1]
		for rrf in rowd:
			fn = rrf[2].replace('=',os.sep)  
			last_file = rrf[0]
			sql2 = '"%s"' % (last_file)
			sql = 'SELECT * FROM linesinfile WHERE  filename='+ sql2+";"
			mysql.query(sql)
			rl = mysql.store_result()
			rowl = rl.fetch_row(0)
			ttt = []
			for rrl in rowl:
				tp = (rrl[2],rrl[3])
				ttt.append(tp)
			dd[fn] = ttt
		if not name in reference.keys():
			reference[name] = dd
		else:
			ddold = reference[name]
			dd.update(ddold)
			reference[name] = dd

	mysql.close()

def merge(mergeFiles,mergeDb,createDB,dbase,v,dfile):
	"""
	loop over mergeFiles and merge Db into a data base
	"""
	global verbose

	verbose = v
	if len(mergeFiles) > 0:
		for f in mergeFiles:
			print "Merge => "+ f
			try:
				fl = open(f,'r')
				ProcessEntryFile(fl)
				fl.close()
				if verbose >= 1:
					print reference
			except IOError:
				print 'File '+f +' cannot be open'

	if len(mergeDb) > 0:
		for f in mergeDb:
			print "Merge => "+ f
			ProcessEntryBase(f)
			if verbose >= 1:
				print reference
	
	if dfile != '':
		try:
			if os.path.exists(dfile):
				os.remove(dfile)
			fref = open(dfile,'w')
			put_in_file('',fref,reference)
			fref.close()
			if os.path.exists(afile):
				os.remove(afile)
			fref = open(afile,'w')
			put_in_afile('',fref,reference)
			fref.close()
		except IOError:
			print 'Cannot open '+dfile+' file'

	if dbase != '':
		put_in_db(dbase,reference,createDB)

def put_in_afile(txt,fd,references):
	allfilesd = buildallfiles(references)
	for j in allfilesd.keys():
		fd.write('file='+j+'\n')
		for n in allfilesd[j]:
			fd.write(n+' ')
		fd.write('\n')
