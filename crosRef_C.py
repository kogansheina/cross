#!/usr/bin/env python

import os
import re
import sys
import time
import cstdlib
import userstdlib

import myutils	
				
DEFINED = 1
USED = 2
MACRO = 4

state = myutils.BEGIN
line_number = 0
verbose = 0
defined_symbols = {}
structcount = 0
substate = myutils.NONE

def parse_for_store_var(o,linearray,vartype,fromdef):
	'''
	receives a string = 0
	linearray - dict with line number as key, and the real line as value
	vartype - defin, macro ,used
	'''
	tpl = myutils.getNames(o)
	for e in tpl:
		lntp = get_line_number(e,linearray)
		if lntp[0] != None:
			store(e,vartype,fromdef,lntp)
		else:
			print "(parse_for_store_var) Error linenumber for "+e+' line number='+str(line_number)
			print o
			print linearray
			sys.exit()

def parse_for_store(line,linearray,vartype):
	'''
	receives a list of possible names and store each of them
	'''
	for o in line:
		parse_for_store_var(o,linearray,vartype,True)

def checkDuplicate(k,tp):
	"""
	 check if the previous tuple is same as parameter
	 in case the same variable is used in the same line more than once
	 returns :
	   0 - file does not exist for this name entry
	   1 - files exists, but tuple not
	   2 - file and tuple exists
	"""
	last = defined_symbols[k] # dict with files as key
	if client in last.keys():
		if tp in last[client]:
			return 2
		return 1
	return 0

def store(n,value,fromdef,lntp):
	"""
	 store the data, if it is not duplicated
	 act different if the name and file exists
	"""
	global defined_symbols

	if n in c_keywords.keys() or n in cstdlib.c_stdlib_api or \
		n in userstdlib.c_userlib_api:
		return 
	if not fromdef:
		if n in userstdlib.c_userlib_var or \
			n in cstdlib.c_stdlib_var:
			return 
	tp = (lntp[0],value,lntp[1])
	try:
		if not n in defined_symbols.keys():
			defined_symbols[n] = {client:[tp]}
		else:
			d = checkDuplicate(n,tp)
			if d == 1: # file already exists, add line
				defined_symbols[n][client].append(tp)
			elif d == 0: # file does not exist
				ft = defined_symbols[n] # files dict
				ft[client]=[tp]
				defined_symbols[n] = ft

	except KeyError:
		print "(store)ERROR=>"+n
		print client+":"+str(lnumber)
		print state
		sys.exit()

def do_nothing(line,linearray):
	for li in range(len(line)):
		l = line[li]
		if len(l) == 0:
			break
		if l in c_keywords.keys():
			c_keywords[l](line[li+1:],linearray)
		else:
			parse_for_store_var(l,linearray,USED,False)

def do_defthing(line,linearray):
	parse_for_store(line,linearray,DEFINED)

def do_casething(line,linearray):
	parse_for_store(line,linearray,USED)

"""
c language reserved words
every callback receives a list of tokens and 
returns the number of list elemets to skip
"""
c_keywords = {
			  "break":do_nothing,
			  "case":do_casething,
			  "char":do_defthing,
			  "const":do_nothing,
			  "continue":do_nothing,
			  "default":do_nothing,
			  "do":do_nothing,
			  "double":do_defthing,
			  "else":do_nothing,
			  "enum":do_defthing,
			  "extern":do_nothing,
			  "float":do_defthing,
			  "for":do_nothing,
			  "goto":do_nothing,
			  "if":do_nothing,
			  "int":do_defthing,
			  "long":do_defthing,
			  "register":do_defthing,
			  "return":do_nothing,
			  "short":do_defthing,
			  "signed":do_nothing,
			  "sizeof":do_nothing,
			  "static":do_nothing,
			  "switch":do_nothing,
			  "typedef":do_nothing,
			  "unsigned":do_nothing,
			  "void":do_defthing,
			  "volatile":do_defthing,
			  "while":do_nothing,
			  "asm":do_nothing,
			  "typeof":do_nothing,
			  "inline":do_nothing,
			  "#define":do_nothing,
			  "struct":do_defthing,
			  "union":do_defthing
			  }

def oneFile(current_file,defsymbols,pathn,v):
	"""
		make the references for one file
	"""
	global line_number,state,substate,defined_symbols,verbose,client,structcount

	linearray = {}
	current_line = ''
	verbose = v
	defined_symbols = defsymbols
	client = pathn
	print "Execute => "+current_file
	try:
		fd = open(current_file,'r')
		line_number = 0
		for line in fd:
			line_number += 1
			if myutils.iscrlf(line):
				continue
			linearray[line_number] = line[:len(line)-1]
			line = line.strip()
			# replace multiple spaces/tabs by one space
			line = myutils.shrinkLine(line) 
			tp = myutils.removeComment(line,substate)
			line = tp[0]
			substate = tp[1]
			if len(line) == 0 or substate == myutils.COMMENT:
				del linearray[line_number]
				continue
			line = myutils.removeStr(line)
			line = line.strip()
			# treat special case that a macro finish with a continuation mark
			if len(line) == 0 and state == myutils.DEFINE:
				process_line(current_line,state,linearray)
				linearray = {}
				current_line = ''
				state = myutils.BEGIN
				continue
			if state == myutils.BEGIN:
				# check for directives; only 'define' is interesting
				if line.startswith('#'):
					if line.startswith('#define'):
						state = myutils.DEFINE
					else:
						if line.startswith('#undef') or line.startswith('#ifdef') or line.startswith('#ifndef'): 
							p = line.find(' ')
							current_line = line[p+1:].strip()
							process_line(current_line,state,linearray)
							linearray = {}
							current_line = ''
							continue
						elif line.endswith('\\'):
							if len(line) == 1:
								continue
							# add the line to current
							current_line += ' '+line[:len(line)-1].strip()
							state = myutils.DEF
							continue
						elif line.startswith('#elif') or line.startswith('#if'):
							p = line.find(' ')
							current_line = line[p+1:].strip()
							process_line(current_line,state,linearray)
						linearray = {}
						current_line = ''
						continue
				# typedef may be followed by struct,union,enum or name - ignore typedef word itself
				elif line.startswith('typedef'):
					line = line[len('typedef'):].strip()
					if line.startswith('struct') or line.startswith('union'):
						state = myutils.STRUCT
					# case of typedef <name> <name> - no mark for end, besides end-of-line
					elif not line.startswith('enum'):
						process_line(line,state,linearray)
						continue
				else:
					if line.startswith('struct') or line.startswith('union'):
						state = myutils.STRUCT
			# *** DEF
			if state == myutils.DEF:
				if line.endswith('\\'):
					if len(line) == 1:
						continue
					# add the line to current
					current_line += ' '+line[:len(line)-1].strip()
				else:
					state = myutils.BEGIN
					process_line(current_line,state,linearray)
					linearray = {}
					current_line = ''
				continue
			# *** DEFINE
			if state == myutils.DEFINE:
				if line.endswith('\\'):
					if len(line) == 1:
						continue
					# add the line to current
					current_line += ' '+line[:len(line)-1].strip()
					# the line is a continuation of the previous
					if line.startswith('#'):
						# the line is another directive - process the previous
						process_line(current_line,state,linearray)
						linearray = {}
						current_line = ''
						linearray[line_number] = line
					# add the line to current
					current_line += ' '+line[:len(line)-1]
				else:
					# end of continuation lines - process
					current_line += ' '+line
					process_line(current_line,state,linearray)
					linearray = {}
					current_line = ''
					state = myutils.BEGIN
			# *** STRUCT
			elif state == myutils.STRUCT:
				if line.endswith('\\'):
					current_line += ' '+line[:len(line)-1].strip()
				else:
					# for struct and union - read into current the entire pattern
					current_line += ' '+line
				pos = line.find('{')
				if pos != -1: # pattern begin
					structcount += 1
				pos = line.find('}')
				if pos != -1: # pattern end
					structcount -= 1
				if structcount == 0: # end, look for ;
					pos1 = line[pos+1:].find(';')
					if pos1 != -1: # everything is in current - process
						process_struct_line(current_line,linearray)
						state = myutils.BEGIN
						linearray = {}
						current_line = ''
				else:
					posopen = current_line.find('(')
					if posopen != -1:
						pos = current_line.find('{')
						if posopen < pos: # it is a function
							state = myutils.BEGIN
							structcount = 0
							ps = current_line.find('struct ')
							current_line = current_line[ps:]
							process_line(current_line,state,linearray)
							linearray = {}
							current_line = ''
			else: # anything else
				if line.endswith('\\'):
					current_line += ' '+line[:len(line)-1].strip()
				elif line.endswith(';'):
					# fill current until ;
					current_line += ' '+line
					process_line(current_line,state,linearray)
					linearray = {}
					current_line = ''
					state = myutils.BEGIN
				else:
					if len(current_line) == 0:
						if not line.startswith('}'):
							current_line += ' '+line

			if verbose > 1:
				print "Original ("+str(line_number)+"): State="+str(state)+" structcount="+str(structcount)
				print current_line

	except IOError:
		print 'File (oneFile) ',current_file,' cannot be open'

	if state != myutils.BEGIN or structcount > 0:
		print "(oneFile)Warning : state="+str(state)+' file: '+current_file+" structcount="+str(structcount)
		state = myutils.BEGIN
		structcount = 0
		sys.exit()
	return defined_symbols

def process_struct_line(line,linearray,debug=False):
	'''
	receives the line - string with all the pattern
	linearray - dict with the original lines and numbers
	'''
	global state
	posi = 0
	line = line.strip()
	if len(line) == 0:
		return
	if line.startswith('struct'):
		posi = len('struct')
	elif line.startswith('union'):
		posi = len('union')
	line = line[posi:].strip()
	# line contains the content of the pattern, without keywords
	if posi > 0: # first time
		pos1 = line.find('{')
		if pos1 >=0 :
			# look for a name after keyword and before definition
			n = line[:pos1].strip()
			if len(n)>0:
				parse_for_store_var(n,linearray,DEFINED,True)
				if '=' in n:
					state = myutils.ARRAYINIT
			pos2 = line.rfind('}')
			if state == myutils.STRUCT:
				pose = line.rfind(';')
				n = line[pos2+1:pose].strip()
				# look for a name after definition and before end
				if len(n)>0:
					parse_for_store_var(n,linearray,DEFINED,True)
			line = line[pos1+1:pos2]
		debug = False
		process_struct_line(line,linearray,debug)
	elif state == myutils.STRUCT:
		posopen = line.find('{')
		posone = line.find(';')
		if debug:
			print '%d:%d' % (posopen,posone)
			print line
		if posopen >= 0 and posone >= 0: # both exist
			if posone < posopen: # regular before new struct or union
				# perform the regular
				linep = line[:posone]
				process_line(linep,myutils.BEGIN,linearray)
				line = line[posone+1:]
				process_struct_line(line,linearray,debug)
			else:
				nesting = line[posopen+1:]
				pos2 = nesting.rfind('}')
				line = nesting[:pos2]
				process_struct_line(line,linearray,debug)
		elif posopen < 0 and posone < 0: # none 
			process_line(line,myutils.BEGIN,linearray)
		elif posopen >=0 : # nesting, without anything else
			nesting = line[posopen+1:]
			pos2 = nesting.rfind('}')
			line = nesting[:pos2]
			process_struct_line(line,linearray,debug)
		else: # no nesting, regular lines
			process_line(line,myutils.BEGIN,linearray)
	else: # struct initialization
		process_struct_array_definition(line,myutils.BEGIN,linearray)

def process_struct_array_definition(line,state,linearray):
	'''
	parse and store the elements of a struct initialization
	'''
	posopen = line.find('{')
	while posopen >= 0:
		posend = line.find('}')
		# perform the regular
		linep = line[posopen+1:posend]
		process_line(linep,myutils.BEGIN,linearray,',')
		line = line[posend+1:]
		posopen = line.find('{')

def process_line(line,state,linearray,c=';'):
	'''
	process lines outside struct or union
	'''
	if state == myutils.BEGIN:
		lline = line.split(';')
		# l is a C regular line, terminated by ;
		for l in lline:
			if len(l) == 0:
				break
			ol = l.strip().split()
			if len(ol) == 0:
				break
			# ol is a list of all element of a logical line
			if ol[0].endswith('*'): # to catch forms as char*, int* ....
				keytrial = ol[0][:len(ol[0])-1]
				if keytrial.endswith('*'): # to catch forms as char**, int** ....
					keytrial = keytrial[:len(keytrial)-1]
			else:
				keytrial = ol[0]
			if keytrial in c_keywords.keys():
				c_keywords[keytrial](ol[1:],linearray)
			elif keytrial in userstdlib.c_userlib_var or keytrial in cstdlib.c_stdlib_var:
				do_defthing(ol[1:],linearray)
			else:
				try:
					for o in ol:
						o = o.strip()
						if (o.startswith("__") and o.endswith("__")) or o == "...": # ignore
							continue
						else:
							parse_for_store_var(o,linearray,USED,False)
				except IndexError:
					print "Index Error : "+o+" in"
					print ol
	elif state == myutils.DEFINE:
		lline = line.split()
		if lline[0] == '#undef':
			lntp = get_line_number(lline[1],linearray)
			if lntp[0] != None:
				store(lline[1],DEFINED,True,lntp)
			else:
				print "(process_line) Error linenumber(1) for "+lline[1]+' line number='+str(line_number)
				print linearray
				sys.exit()
		else:
			pos = lline[1].find('(')
			if pos == -1: # not macro
				lntp = get_line_number(lline[1],linearray)
				if lntp[0] != None:
					store(lline[1],DEFINED,True,lntp)
				else:
					print "(process_line) Error linenumber(2) for "+lline[1]+' line number='+str(line_number)
					print line
					print linearray
					sys.exit()
			else:
				lntp = get_line_number(lline[1][:pos],linearray)
				if lntp[0] != None:
					store(lline[1][:pos],MACRO,True,lntp)
				else:
					print "(process_line) Error linenumber(3) for "+lline[1][:pos]+' line number='+str(line_number)
					print linearray
					sys.exit()
			for l in lline[2:]:
				parse_for_store_var(l,linearray,USED,False)
	else:
		print "(process_line) State error = %d linenumber = %d " % (state,line_number)
		print line
		print linearray
		sys.exit()

def get_position(n,tofind):
	'''
	return a list of positions of n into line tofind
	'''
	pos = tofind.find(n)
	positions = []
	while pos >= 0:
		if not tofind[pos-1:pos].isalnum() and tofind[pos-1:pos] != "_" and \
		   not tofind[pos+len(n):pos+len(n)+1].isalnum() and tofind[pos+len(n):pos+len(n)+1] != "_":
			positions.append(pos)
		pos1 = tofind[pos+len(n):].find(n)
		if pos1 >= 0:
			pos = pos1 + pos + len(n)
		else:
			pos = -1
	return positions

def get_line_number(n,ar):
	'''
	looks for n in ar dict and return real line number
	'''
	for ak,av in ar.items():
		avlist = av.split()
		if n in avlist:
			return (ak,get_position(n,av))
		for a in avlist:
			tofind = a
			pos = tofind.find(n)
			while pos >= 0:
				if pos > 0:
					if not tofind[pos-1:pos].isalnum() and tofind[pos-1:pos] != "_" and \
					   not tofind[pos+len(n):pos+len(n)+1].isalnum() and tofind[pos+len(n):pos+len(n)+1] != "_":
						return (ak,get_position(n,av))
				elif not tofind[len(n):len(n)+1].isalnum() and tofind[len(n):len(n)+1] != "_":
						return (ak,get_position(n,av))
				tofind = tofind[pos+len(n):]
				pos = tofind.find(n)
	return (None,None)



