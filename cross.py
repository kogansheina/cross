#!/usr/bin/env python

import os
import re
import sys
import time
import random
import myutils

current_file = ""
fileseparator = '/'	# os.sep				
# dictionary key = variable name
# value is a dictionary with file name as key 
# and value a list of tuples
# each tuple is line number and type (defintion or/and usage)
mergeFiles = []
mergeDb = []					
defined_symbols = {}					
verbose = 0
pathname = ''
dbase = ''
dfile = ''
afile = ''
createDB = False
client = None
lastdir = ''
initial_pathname = ''
tmpdir = ''
skipdirs = {} # key=dir to skip, value=list of except directories

startStr = ""

import crosRef_db
import crosRef_C
from myutils import iscrlf

help = "usage : <command> <options>\n\
		cpmmands : -help -merge -top -file -s\n\
		options : -skip -except -db -du -v\n\n\
		to see more explanation use -help command"
helpLong = " -merge command needs a list of *.ref files or/and *_pyt data bases\n\
 -s command receives a script file containing any other commands\n\
 -file command receives a file name(absolute path)\n\
 -top command receives a directory path(absolute path)\n\
 -skip option goes only for -top command; receives a directory path relative to top directory\n\
    may be many such options; those directories will be skipped from analizing\n\
 -except option goes only for -top command; receives a directory path relative to previous skip directory\n\
    may be many such options; those directories will be analized anyway\n\
 -db options receives a data base name to be created(it adds sufix _pyt)\n\
 -du options receives a data base name to be updated(look for <name>_pyt)\n\
 -df options receives a file name name to be created(it adds suffix .ref), does not work for -merge\n\
 -v receives a verbose level <0 | 1 | 2 | 3>]\n\n"

def get_real_path():

	if client != None: # replace the temp path with the svn one
		ii = current_file[len(pathname):]
		ii = ii.replace(fileseparator,'/')
		jj = initial_pathname+'/'+ii
	else:
		jj = current_file
	return jj

def ProcessEntry(path,files):
	"""
		update defined_symbols dict with a list of tulples : {file: list of (line,type)}
	""" 		
	global current_file,defined_symbols

	if not path.endswith(fileseparator):
		current_path = path + fileseparator
	else:
		current_path = path
	for f in files:
		current_file = current_path + f	
		if not current_file.endswith('.c') and not current_file.endswith('.h'):
			continue
		if  current_file.endswith('.mod.c'):
			continue
		defined_symbols = crosRef_C.oneFile(current_file,defined_symbols,get_real_path(),verbose)

def parseargs(args):
	"""
		parse running arguments
	"""
	global pathname,current_file,initial_pathname,tmpdir
	global dbase,dfile,afile
	global skipdirs
	global verbose,createDB
	global mergeFiles,mergeDb
	
	exceptdirs = []
	skipdir = ''
	command = 0
	i = 1
	if args[0] == '-help':
		print helpLong
		sys.exit()

	if args[0] == '-merge':
		command = 1
		while (i < len(args)-1):
			if args[i].startswith('-'):
				break
			elif args[i].endswith('.ref'):
				mergeFiles.append(args[i])
			elif args[i].endswith('_pyt'):
				mergeDb.append(args[i])
			else:
				print "-merge receives *.ref files or *_pyt data bases : "+args[i]
				print help
				return False
			i += 1
	elif args[0] == '-top':
		command = 2
		if len(args) >= 2:
			pathname = args[1]
			initial_pathname = pathname
			i += 1
			if not pathname.startswith("http:"):
				if not pathname.endswith(fileseparator):
					pathname += fileseparator
			else:
				tmpdir = '.'+fileseparator+'tmptop'+str(random.randint(1,100))
				pathname = tmpdir+fileseparator
		else:
			print "Wrong number of parameters"
			print help
			return False
	elif args[0] == '-file':
		command = 3
		if len(args) >= 2:
			current_file = args[1]
			i += 1
			if not current_file.endswith('.c') and not current_file.endswith('.h'):
				print "Tool only for *.c or *.h files"
				return  False
		else:
			print "Wrong number of parameters"
			print help
			return False
	else:
		print 'Unknown command '+ args[0]
		print help

	if len(args) > 2: # top command
		if len(args[i:]) % 2 != 0: 
			print "Number of arguments must be even"
			print args[i:]
			print help
			return False
		restarg = args[i:]
		for i in range(0,len(restarg),2):
			if restarg[i] == '-except':
				if command == 2:
					if len(skipdir) == 0:
						print '-except must have a precedent -skip'
						print help
						return False
					else:
						exceptdirs.append(restarg[i+1])
				else:
					print "Option -except goes only for -top command, ignored"
			elif restarg[i] == '-skip':
				if command == 2:
					if len(pathname) == 0:
						print 'Top directory must be declared before any -skip parameter'
						print help
						return False
					if len(skipdir) != 0:
						skipdirs[skipdir] = exceptdirs
						exceptdirs = []
					skipdir = pathname+restarg[i+1]
				else:
					print "Option -skip goes only for -top command, ignored"
			elif restarg[i] == '-db' or restarg[i] == '-du':
				if myutils.isName(restarg[i+1]):
					dbase = restarg[i+1]+'_pyt'
					if restarg[i] == '-db':
						createDB = True
				else:
					print 'DB name must begin with letter and may contain only alphacharacters and "_" character : "'+restarg[i]+'"'
					return	 False		
			elif restarg[i] == '-df':
				dfile = restarg[i+1]+'.ref'
				afile = restarg[i+1]+'.auxref'
			elif restarg[i] == '-v':
				verbose = int(restarg[i+1])
			else:
				print "Unknown option " + restarg[i] + ", ignored"
			
	if (len(mergeFiles)!=0 or len(mergeDb)!=0):
		if (current_file != '') or (pathname != ''):
			print "Merge option is exclusive with -file and -top options"
			print help
			return False

	if len(skipdir) != 0:
		skipdirs[skipdir] = exceptdirs
				
	return True

def main(argv):
	"""
		MAIN
	"""				
	global pathname
	global dbase,dfile
	global defined_symbols,skipdirs
	global verbose,current_file
	global client,lastdir,initial_pathname

	args = []
	if len(argv) == 1:
		print "Wrong number of arguments"
		print help
		return
	if argv[1] == '-s': # script
		try:
			fd = open(argv[2],'r')
			for line in fd:
				if iscrlf(line):
					continue
				if line.strip().startswith('#'):
					continue
				args.extend(line.strip().split())
			fd.close()
		except IOError:
			print 'Cannot open '+argv[2]+' script file'
			return	
	else:	
		args = argv[1:]
	if not parseargs(args):
		return
	if (len(pathname) == 0 and len(current_file) == 0) and (len(mergeFiles) == 0 and len(mergeDb) == 0):
		print 'Top directory or File name or Merge lists is mandatory'
		print help
		return
	if len(pathname) != 0 and len(current_file) != 0:
		print 'Only one option may be used : -top or -file'
		print help
		return
	start = time.time()	
	if len(mergeFiles) != 0 or len(mergeDb)!= 0:
		crosRef_db.merge(mergeFiles,mergeDb,createDB,dbase,verbose,dfile)
	else:
		if len(pathname) > 0:
			if not initial_pathname.startswith("http:"):
				if not os.path.isdir(initial_pathname):
					print 'Top must be a directory : '+initial_pathname	
					return	
				if not os.path.exists(initial_pathname):
					print initial_pathname + ' does not exists'
					return		
			else:
				import pysvn
				client = pysvn.Client()
				client.export( initial_pathname,tmpdir)
				lastdiri = initial_pathname.rfind('/')
				if lastdiri != -1:
					lastdir = initial_pathname[lastdiri:]
				else:
					lastdir = initial_pathname	
			for root, dirs, files in os.walk(pathname):
				if len(root) > 0 :
					if '.svn' in dirs: dirs.remove('.svn')
					if '.metadata' in dirs: dirs.remove('.metadata')
					if root.endswith(fileseparator): 
						pp = root
						root = root[:len(root)-1]
					else:
						pp = root+fileseparator
				toremove = []
				for y in dirs:
					py = pp+y
					if py in skipdirs.keys():
						if len(skipdirs[py]) == 0:
							toremove.append(y)
				for y in toremove:			
					if verbose >= 1: print 'remove : ' + y + ' from ' + root
					dirs.remove(y)
				if root in skipdirs.keys(): # skip directory; check for except
					toremove = []
					for y in dirs:
						if not y in skipdirs[root]:
							toremove.append(y)
					for y in toremove:
						if verbose >= 1: print 'remove : ' + y + ' from ' + root
						dirs.remove(y)
				else:
					if len(files) > 0:
						ProcessEntry(root,files)
		else:
			defined_symbols = crosRef_C.oneFile(current_file,defined_symbols,get_real_path(),verbose)
			pathname = os.path.dirname(current_file)+fileseparator
			current_file = os.path.basename(current_file)

		if dfile != '':
			try:
				if os.path.exists(dfile):
					os.remove(dfile)
				fref = open(dfile,'w')
				crosRef_db.put_in_file('',fref,defined_symbols)
				fref.close()
				if os.path.exists(afile):
					os.remove(afile)
				fref = open(afile,'w')
				crosRef_db.put_in_afile('',fref,defined_symbols)
				fref.close()
			except IOError:
				print 'Cannot open '+dfile+' output file'
			
		if dbase != '':
			crosRef_db.put_in_db(dbase,defined_symbols,createDB)

		if dfile == '' and dbase == '':
			crosRef_db.put_in_file('',sys.stdout,defined_symbols)

		if client:
			import shutil
			shutil.rmtree(pathname)
			"""
			for root, dirs, files in os.walk(pathname):
				for f in files:
					os.remove(root+fileseparator+f)
			for root, dirs, files in os.walk(pathname):
				if len(dirs) == 0:
					os.rmdir(root)
			"""
			
	print 'Elapsed time (seconds) = ' + str(time.time()-start)
##########################################################################																	
if __name__ == '__main__':
	from sys import argv
	main(argv)
