#!/usr/bin/env python
from BeautifulSoup import BeautifulSoup
import urllib2
import re
import os
import sys
import Tkinter
import thread

def guiWrite(buff):
	global xOut
	if xOut != None:
		xOut.insert(Tkinter.END, buff+'\n')
		xOut.yview(Tkinter.END)
	else:
		print buff

xOut = None

def guiStart():
	global xOut
	app = Tkinter.Tk()
	app.title("Chomik mp3 downloader")
	app.geometry('580x410+200+20')
	xOut = Tkinter.Text(app)
	xOut.insert(Tkinter.END, "")
	xOut.pack()

	def gogogo():
		urls = xOut.get(1.0,Tkinter.END)[:-1]
		xOut.delete(1.0, Tkinter.END)
		thread.start_new_thread(downloadRecursive,(urls,))

	abutton = Tkinter.Button(app, text="Rozpocznij", command=gogogo)
	abutton.pack()
	app.mainloop()

_getLinksVisited = []
def getLinks(url):
	if _getLinksVisited.count(url) == 0:
		_getLinksVisited.append(url)
	else:
		return list()
	guiWrite( "Looking for links in %s"%url )
	links = [] 
	html = urllib2.urlopen(url)
	soup = BeautifulSoup(html)
	for div in soup.findAll('div',attrs={'id':'folderContent'}):
		attrs = {k:v for (k,v) in div.attrs }
		if attrs.has_key('id') and attrs['id'] == 'folderContent':
			# grabowanie linkow
			for link in div.findAll('a',attrs={'href': re.compile("^.*\(audio\)$")}):
				links.append(link.get('href'))
	return list(set(links))

_getSubDirsVisited = []
def getSubDirs(url):
	if _getSubDirsVisited.count(url) == 0:
		_getSubDirsVisited.append(url)
	else:
		return list()
	guiWrite( "Looking for subdirs in %s"%url )
	dirs = []
	html = urllib2.urlopen(url)
	soup = BeautifulSoup(html)
	for div in soup.findAll('div',attrs={'id':'folderContent'}):
		attrs = {k:v for (k,v) in div.attrs }
		if attrs.has_key('id') and attrs['id'] == 'folderContent':
			# podfoldery ? ;)
			for subdiv in div.findAll('div',attrs={'id':'foldersList'}):
				subattrs = {k:v for (k,v) in subdiv.attrs }
				if subattrs.has_key('id') and subattrs['id'] == 'foldersList':
					for dirLink in subdiv.findAll('a'):
						dirs.append(dirLink.get('href'))
	return list(set(dirs))
def downloadFileTo(srcFile,dstFile):
	try:
		os.makedirs('/'.join(dstFile.split('/')[:-1]))
	except Exception, e:
		pass
	dst = open(dstFile,'w')
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]
	response = opener.open(srcFile)
	meta = response.info()
	file_size = int(meta.getheaders("Content-Length")[0])
	r = 0.0
	guiWrite(dstFile+'\n\r')
	barSize = 30
	guiTgt = [True]*11
	while True:
		buf = response.read(8192)
		if buf == '':
			break
		dst.write(buf)
		r+=len(buf)
		now = r*barSize/file_size
		sys.stdout.write('\r[')
		for i in xrange(int(now)):
			sys.stdout.write('=')
		for i in xrange(int(barSize-now)):
			sys.stdout.write(' ')
		p = int(r*100/file_size)
		if p%10 == 0 and guiTgt[p/10]:
			guiTgt[p/10] = False
			guiWrite('Pobrano %d%c'%(p,'%'))
		sys.stdout.write('] %d%c'%(p,'%'))
		sys.stdout.flush()
	sys.stdout.write('\n')
	dst.close()
	response.close()

def getRecursiveLinks(src):
	_stripPrefix = 'http://chomikuj.pl'
	links = []
	for subDir in getSubDirs(src):
		links += getRecursiveLinks(_stripPrefix+subDir)
	links += [_stripPrefix+link for link in getLinks(src)]
	return list(set(links))

def getDownloadParams(link,baseLink):
	chomikujBase = 'http://chomikuj.pl/Audio.ashx?id=%s&type=2&tp=mp3'
	replaces = {
		'+':'_',
		':':'-',
		'?':'_',
		'*27':'\'',
		'*2c':',',
		'*c4*99':'e',
		'*c5*9b':'s',
		'*c4*87':'c',
		'*c3*b3':'o',
		'*c5*ba':'z',
		'*c5*82':'l',
		'*c5*81':'L',
		'*c5*84':'n',
		'*26':'&',
		'*c4*85':'a',
		'*c4*a4':'a',
		'*c5*9b':'s'
	}
	m = re.match(r"^(?P<user>.+)/(?P<path>.+)/(?P<name>.+),(?P<id>.+)\.(?P<ext>.+)\(audio\)$",link)
	if m:
		if baseLink[-1] != '/':
			baseLink += '/'
		info = m.groupdict()
		downloadLink = chomikujBase%info['id']
		name = "%s.%s"%(info['name'],info['ext'])
		target = '/'.join(link.replace(baseLink,'').split('/')[:-1])
		for (f,t) in zip(replaces.keys(),replaces.values()):
			name = name.replace(f,t)
			target = target.replace(f,t)
		if target != '':
			target = target + '/'
		return (downloadLink,target,name)
	return	None

def downloadRecursive(url):
	todo = getRecursiveLinks(url)
	i = 0
	for link in todo:
		i += 1
		guiWrite( 'Downloading link %d of %d...'%(i,len(todo)) )
		p = getDownloadParams(link,url)
		if p != None:
			downloadFileTo(p[0],p[1]+p[2])
		
def main():
	src = sys.argv[-1]
	downloadRecursive(src)
	# guiStart()

if __name__ == "__main__":
	main()