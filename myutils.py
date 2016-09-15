#!/usr/bin/env python
import re
startStr = ""
# states
NONE = 0
BEGIN = 3
COMMENT = 1
STRUCT = 2
DEF = 4
DEFINE = 5
ARRAYINIT = 6
mysqluser = "root" # reggae(work) root(home)
mysqlpwd = "" # bl5768(work) ''(home)

def shrinkLine(line):
	"""				
	 replace multiple tabs by one space
	"""
	j = line.split("\t")
	l = []
	for k in j:
		if k != '':
			l.append(k)
	return " ".join(l)

def toHex(s):
	"""
	convert string to hex
	"""
	lst = []
	for ch in s:
		hv = hex(ord(ch)).replace('0x', '')
		if len(hv) == 1:
			hv = '0'+hv
		lst.append(hv)
	return "".join(lst)

def toStr(s):
	"""
	convert hex repr to string
	"""
	return s and chr(atoi(s[:2], base=16)) + toStr(s[2:]) or ''

def iscrlf (lineO):
	"""
	check if it is an 'empty' string
	"""
	if len(lineO) == 0: 
		return True
	if lineO == '\n' or lineO == '\r' or \
		lineO == '\n\r' or lineO == '\r\n':
		return True
	return False

def isName (l):
	"""
	check if the string has the format on a legal variable
	"""
	if len(l) == 0:
		return False
	name = re.match(r'[A-Za-z_][A-Za-z_0-9]*',l)
	try:
		n = name.group(0)
		if n==l:
			return True
		return False
	except AttributeError:
		return False

def removeComment(lineToClean,substate,debug=False):
	"""
	remove recursively comments and
	returns a line without comments, or substate
	comment, for the cases when a comment lies on more than one line
	"""
	if len(lineToClean) == 0:
		return (lineToClean,substate)

	line = lineToClean
	if startStr == "":
		pos = line.find("//")
		if pos != -1:
			return (line[:pos],substate)
		poss = line.find("/*")
		pose = line.find("*/")
		if poss != -1:
			if pose != -1: # both exists in line - check which is first
				if pose >= poss+2: # regular comment - remove it and continue
					line = line[0:poss] + line[pose+2:]
					tp = removeComment(line,substate,debug)
					line = tp[0]
					substate = tp[1]
				elif pose > poss: # case /*/.....*/
					pose = line[poss+2:].find("*/")
					line = line[0:poss] + line[pose+2+poss+2:]
					tp = removeComment(line,substate,debug)
					line = tp[0]
					substate = tp[1]
				else: # close comment and remove only until closure
					substate = NONE
					line = line[pose+2:]
					tp = removeComment(line,substate,debug)
					line = tp[0]
					substate = tp[1]
			else: # only start exists, set state and return empty
				substate = COMMENT
				line = ''
		elif substate == COMMENT: # only end exists
			pos = line.find("*/")
			if pos != -1:
				substate = NONE
				line = line[pos+2:]
				tp = removeComment(line,substate,debug)
				line = tp[0]
				substate = tp[1]

	return (line,substate)

def removeStr(lineToClean,debug=False):
	"""
	remove string from the line
	takes care of strings on multiple lines
	"""
	global startStr

	if len(lineToClean) == 0:
		return lineToClean

	line = lineToClean
	if startStr == "":
		poss = line.find('"')
		if poss != -1: 
			c = line[poss:poss+1]
			if poss < len(line):
				pose = line[poss+1:].find(c)
				if pose != -1: # the string finishes on the same line it started
					return removeStr(line[:poss]+line[poss+pose+2:],debug)
			else:
				startStr = c
				return line[:poss]
		else:
			pos = line.find("'")
			if pos != -1:
				rest = line[pos+1:]
				pose = rest.find("'")
				pose += pos+1
				if debug:
					print 'removeStr'
					print line[:pos]
					print line[pose+1:]
				line = line[:pos]+line[pose+1:] # remove 'x'
	else: # middle of a string
		posc = line.find(startStr)
		if posc != -1:
			startStr = ""
			return removeStr(line[posc+1:],debug)
		else:
			return ""

	return line

def someConst(c):
	"""
	check if the string represents some kind of constant
	as 0x or 0X (hex) o or O (octals) 0b or 0B (binary)
	digits or characters or strings
	"""
	if c[0].isdigit():
		return True
	elif c.lower().startswith("o"):
		for cc in c[1:]:
			if not cc.isdigit():
				return False
		else:
			return True
	elif c.startswith("'") and c.endswith("'"):
		return True
	elif c.startswith('"') and c.endswith('"'):
		return True
	return False

def getNames (line):
	"""
	 returns a list of tokens
	 ignore tokens in string
	 detect the end of an enum 
	"""
	linelist = line.split()
	final = []
	last = ""
	for c in linelist:
		if someConst(c):
			continue
		if isName(c):
			final.append(c)
		else:
			tmp = []
			for ch in c:
				if ch.isalnum() or ch == "_":
					tmp.append(ch)
				else:
					if len(tmp) > 0:
						if ch == "'" or ch == '"':
							last = ch + "".join(tmp) + ch
						else:
							last = "".join(tmp)
						if not someConst(last):
							final.append(last)
						tmp = []
			if len(tmp) > 0:
				last = "".join(tmp)
				if not someConst(last):
					final.append(last)
	return final

