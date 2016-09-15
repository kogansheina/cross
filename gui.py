#!/usr/bin/env python
import os
import sys
from Tkinter import *
import tkFont
import tkMessageBox,tkFileDialog
import myutils	
import MySQLdb as DB
titleFont = ("Arial", 12, "bold italic")
regularFont = ("Arial", 12)

class doIt():
	def __init__(self, fn,root,db=None):
		self.windowsList = []
		self.frame = Frame(root)
		self.root = root
		self.source = True
		if fn:
			filename = fn
		else:
			self.source = False
			filename = db
		self.root.title(filename)
		if self.source:
			file = open(filename,'r')
			filename=filename.replace('.ref','.auxref')
			fileaux = open(filename,'r')
			tp = self.buildDataBase(file,fileaux)
			self.mydb = tp[0]
			self.myfiles = tp[1]
			file.close()
			fileaux.close()
		else:
			self.mysql = DB.connect(host="127.0.0.1",user=myutils.mysqluser,passwd=myutils.mysqlpwd) 
			self.mysql.select_db(db)
			self.mydb = db
			self.myfiles = db
			self.cr = mysql.cursor()
		self.oldvar = None
		self.end = False
		self.lookfor = StringVar()
		self.we = Entry(self.frame,width=80,bg="yellow",textvariable=self.lookfor)
		self.we.bind("<Return>",self.look_for_tables)
		self.we.pack()
		self.we.focus_set()
		self.frame.pack()
		self.topw = None
		self.tags = 0

	def displayVars(self,found):
		s = Scrollbar(self.topw)
		t = Text(self.topw,bg='#f8e8a0',width=140)
		t.focus_set()
		s.pack(side=RIGHT,fill=Y)
		t.pack(side=LEFT,fill=BOTH,expand=YES)
		s.config(command=t.yview)
		t.config(yscrollcommand=s.set,font=regularFont)
		def on_mousewheel(event,s=s):
			return self._on_mousewheel(event,s)
		self.topw.bind_all("<MouseWheel>", on_mousewheel)
		cc = 1
		for name in found:
			if self.source:
				vals = self.mydb[name]
			else:
				sql1= '"%s"' % (name)
				sql = "SELECT * FROM names WHERE name="+ sql1+";"
				cr.execute(sql)
				mysql.commit()
				row = cr.fetchone()
				if row != None:
					sql2 = '"%d"' % (row[0])
					sql = 'SELECT * FROM files WHERE  name='+ sql2+";"
					cr.execute(sql)
					rowd = cr.fetchall()
			t.tag_add("name",str(cc)+".0",str(cc)+"."+str(len(name)))
			t.tag_configure("name",foreground='brown',font=titleFont)
			t.insert(END,name+'\n',"name")
			cc += 1
			if self.source:
				for f,vlines in vals.iteritems():
					t.insert(END,'    '+f+'\n    ')
					cc += 1
					dd = 0
					for tp in vlines:
						nlinel = tp[0].split(':')
						nline = nlinel[0]
						tline = tp[1] # f+nline
						t.tag_add(f+nline,str(cc)+".0",str(cc)+"."+str(len(nline)+1))
						t.tag_configure(f+nline,foreground='blue')
						def handler(event, n=name, fn=f, l=nline):
							return self.entryhandler(n,fn,l)
						t.tag_bind(f+nline,"<Button-1>",func=handler)
						t.insert(END,nline,f+nline)
						dd += 1
						if dd == 16:
							cc += 1
							t.insert(END,' '+tline+'\n    ')
							dd = 0
						else:
							t.insert(END,' '+tline+'   ')
					cc += 1
					t.insert(END,'\n')
			else:
				for fj in xrange(0,len(rowd),2):
					fn = rowd[fj]
					f = rowd[fj+1]
					f = f.replace('=','/')
					t.insert(END,'    '+f+'\n    ')
					cc += 1
					dd = 0
					sql2 = '"%d"' % (fn)
					sql = 'SELECT * FROM files WHERE  filename='+ sql2+";"
					cr.execute(sql)
					rowl = cr.fetchall()
					for l in xrange(0,len(rowl),2):
						nlinel = rowl[l].split(':')
						nline = nlinel[0]
						tline = rowl[l+1] # f+nline
						t.tag_add(f+nline,str(cc)+".0",str(cc)+"."+str(len(nline)+1))
						t.tag_configure(f+nline,foreground='blue')
						def handler(event, n=name, fn=f, l=nline):
							return self.entryhandler(n,fn,l)
						t.tag_bind(f+nline,"<Button-1>",func=handler)
						t.insert(END,nline,f+nline)
						dd += 1
						if dd == 16:
							cc += 1
							t.insert(END,' '+tline+'\n    ')
							dd = 0
						else:
							t.insert(END,' '+tline+'   ')
					cc += 1
					t.insert(END,'\n')
		self.topw.pack()

	def _on_mousewheel(self, event,s):
		# -120 is down ; +120 is up
		s.yview_scroll(-1*(event.delta/120), "units")

	def look_for_tables(self,event):
		'''
		actually does the serach
		'''
		self.lookfor = self.we.get()
		tofind = self.lookfor.lower()
		star = 0
		found = []
		if tofind.startswith('*'):
			tofind = tofind[1:]
			star = 1
		if tofind.endswith('*'):
			tofind = tofind[:len(tofind)-1]
			if star == 1:
				star = 3
			else:
				star = 2
		for i in self.mydb.keys():
			j = i
			i = i.lower()
			if star == 1:
				if tofind == i[len(i)-len(tofind):]:
					found.append(j)
			elif star == 2:
				if tofind == i[:len(tofind)]:
					found.append(j)
			elif star == 3:
				if tofind in i:
					found.append(j)
			else:
				if tofind == i:
					found.append(j)
		if len(found) == 0:
			tkMessageBox.showwarning("Warning",self.lookfor+" was not found")
		else:
			if self.oldvar != None:
				self.topw.destroy()
			self.oldvar = self.lookfor
			# display only the found tables
			self.topw=LabelFrame(master=self.frame,labelanchor='n',text=self.lookfor)
			self.displayVars(found)

	def quitwindow(self,name):
		'''
		close window handler (all the new ones) - not the main
		closeing the main - will close all its children
		'''
		for topw in self.windowsList:
			if name == topw.title:
				self.windowsList.remove(topw)
				topw.destroy()
				if not self.source:
					self.cr.close()
					self.mysql.close()
				break

	def positions(self,filename,linenumber):
		'''
		input : file name, line number
		output: sorted list of tuples
		each tuple : (start,end)
		'''
		retlist = []
		namelist = self.myfiles[filename] # list of names in file
		for n in namelist:
			all = False
			tplist = self.mydb[n][filename] # list of tuples (ln:pos:pos..,type) for name in file
			for tp in tplist:
				if all:
					break
				ltmp = tp[0]
				listl = ltmp.split(':') # list : line number, pos1,pos2,....
				ln = listl[0]  # line number
				if int(ln) == linenumber:
					lpos = listl[1:] # list of positions in line of the name=n
					for p in lpos:
						start = int(p)
						end = start+len(n)
						if len(retlist) == 0:
							retlist.append((n,start,end))
						else:
							done = False
							for l in xrange(0,len(retlist)):
								if done:
									break
								eltp = retlist[l]
								elstart = eltp[0]
								if start > elstart:
									retlist.insert(l,(n,start,end))
									done = True
							if not done:
								retlist.append((n,start,end))
					all = True
					break
		return retlist

	def displayDefinition(self,file,line,name):
		print "displayDefinition:"+file
		ffile = open(file,'r')
		ln = 1
		linelist = line.split(':')
		lnumber = int(linelist[0])
		top=Toplevel(master=self.root)
		top.title(file)
		def nextwindow_handler(name=top.title):
			return self.quitwindow(name)
		top.protocol("WM_DELETE_WINDOW", nextwindow_handler)
		self.windowsList.append(top)
		s = Scrollbar(top)
		t = Text(top,bg='#f8e8a0',width=120)
		t.focus_set()
		s.config(command=t.yview)
		t.config(yscrollcommand=s.set,font=('helvetica','12'))
		for l in ffile:
			txt = "%d:\t" % (ln)
			if ln == lnumber:
				startpos = '%d.%d' % (ln,0)
				endpos = '%d.%d' % (ln,len(txt))
				t.tag_add('highlightline1',startpos,endpos)
				t.tag_configure('highlightline1',foreground='red')
				t.insert(END,txt,'highlightline1')
				pos = int(linelist[1])
				t.insert(END,l[:pos])
				startpos = '%d.%d' % (ln,pos+len(txt))
				endpos = '%d.%d' % (ln,pos+len(name)+len(txt))
				t.tag_add('highlightline2',startpos,endpos)
				t.tag_configure('highlightline2',foreground='red')
				t.insert(END,l[pos:pos+len(name)],'highlightline2')
				t.insert(END,l[pos+len(name):])
				if ln > 15:
					s.config(command=t.yview(ln-15))
			else:
				t.insert(END,txt+l)
			ln += 1
		ffile.close()
		def on_mousewheel(event,s=s):
			return self._on_mousewheel(event,s)
		top.bind_all("<MouseWheel>", on_mousewheel)
		s.pack(side=RIGHT,fill=Y)
		t.pack(side=LEFT,fill=BOTH)

	def entryhandler(self, name, filename, linenumber):
		print "entryhandler:"+filename
		ffile = open(filename,'r')
		ln = 1
		lnumber = int(linenumber)
		top=Toplevel(master=self.root)
		top.title(filename)
		def nextwindow_handler(name=top.title):
			return self.quitwindow(name)
		top.protocol("WM_DELETE_WINDOW", nextwindow_handler)
		self.windowsList.append(top)
		s = Scrollbar(top)
		t = Text(top,bg='#f8e8a0',width=120)
		t.focus_set()
		s.config(command=t.yview)
		t.config(yscrollcommand=s.set,font=('helvetica','12'))
		for l in ffile:
			txt = "%d:\t" % (ln)
			if ln == lnumber:
				startpos = '%d.%d' % (ln,0)
				endpos = '%d.%d' % (ln,len(txt))
				t.tag_add('highlightline',startpos,endpos)
				t.tag_configure('highlightline',foreground='red')
				t.insert(END,txt,'highlightline')
				if ln > 15:
					s.config(command=t.yview(ln-15))
			else:
				t.insert(END,txt)
			poslist = self.positions(filename,ln)
			crtpos = 0
			if len(poslist):
				print ln
				print poslist
			for postp in poslist:
				if postp[1] >= crtpos:
					# insert before
					t.insert(END,l[crtpos:postp[1]])
				vals = self.mydb[postp[0]]
				deftuple = 0
				fdef = ''
				for f,tapsl in vals.iteritems():
					if fdef != '':
						break
					for taps in tapsl:
						typ = taps[1]
						if typ != 'refer':
							deftuple = taps[0]
							fdef = f
							break
				startpos = '%d.%d' % (ln,len(txt)+postp[1])
				endpos = '%d.%d' % (ln,len(txt)+postp[2])
				tag = str(self.tags)
				t.tag_add(tag,startpos,endpos)
				t.tag_configure(tag,foreground='blue')
				t.insert(END,l[postp[1]:postp[2]],tag)
				crtpos = postp[2]
				def definition(event,file=fdef, line=deftuple,n=postp[0]):
					return self.displayDefinition(file,line,n)
				#def definition(event,name=n):
				#	return self.displayVars([name])
				t.tag_bind(tag,"<Button-1>",func=definition)
				self.tags += 1
			t.insert(END,l[crtpos:])
			ln += 1
		ffile.close()

		def on_mousewheel(event,s=s):
			return self._on_mousewheel(event,s)
		top.bind_all("<MouseWheel>", on_mousewheel)
		s.pack(side=RIGHT,fill=Y)
		t.pack(side=LEFT,fill=BOTH)

	def buildDataBase(self,file,fileaux):
		db = {}
		files = {}
		allfiles = {}
		lines = []
		name = None
		filename = None
		state = 0
		for line in file:
			line = line.strip()
			if line.startswith('name='):
				if state:
					files[filename] = lines
					db[name] = files
					files = {}
					'''
					if state == 3:
						if filename in allfiles.keys() and not name in allfiles[filename]: 
							allfiles[filename].append(name)
						else:
							allfiles[filename]=[name]
					'''
				name = line[len('name='):]
				state = 1
			elif line.startswith('file='):
				if len(lines) > 0:
					if state == 3:
						files[filename] = lines
						'''
						if filename in allfiles.keys() and not name in allfiles[filename]: 
							allfiles[filename].append(name)
						else:
							allfiles[filename]=[name]
						'''
					lines = []
				state = 2
				filename = line[len('file='):]
			else:
				lineparams = line.split()
				for l in lineparams:
					if l.startswith('line='):
						nline = l[len('line='):]
					else:
						tline = l[len('type='):]
						lines.append((nline,tline))
				state = 3
		if len(lines):
			files[filename] = lines
			db[name] = files
		#for a in db.keys():
		#	if a == 'xlp_set_gpio_41':
		#		print a
		#		for b in db[a].keys():
		#			print b
		#			print db[a][b]
		state = 0
		lines = []
		for line in fileaux:
			line = line.strip()
			if line.startswith('file='):
				if state:
					allfiles[filename] = lines
					lines = []
				filename = line[len('file='):]
				state = 1
			else:
				lines = line.split()

		#for a in allfiles.keys():
		#	print a 	
		#	print allfiles[a]
	
		return (db,allfiles)

if __name__ == '__main__':
	root = Tk()
	filename = tkFileDialog.askopenfilename(defaultextension='.ref', initialdir='./refs', parent=root, title='Choose reference file')
	if filename:
		doIt(filename,root)
	else:
		v = StringVar()
		def doOne():
			return doIt(None,root,v.get())
		mysql = DB.connect(host="127.0.0.1",user=myutils.mysqluser,passwd=myutils.mysqlpwd) 
		cr = mysql.cursor()
		cr.execute('show databases;')
		mysql.commit()
		row = cr.fetchone()
		first = False
		while row:
			if row[0].endswith('_pyt'):
				Radiobutton(root, text=row[0][:len(row[0])-4], variable=v, value=row[0], command=doOne).pack(anchor=W)
			row = cr.fetchone()
		#try:
		#	mysql.select_db(dbase)
		#except : 
		#	print 'DataBase '+dbase+ ' does not exist'
		#	sys.exit()
	root.mainloop()
