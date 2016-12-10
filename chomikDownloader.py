from BeautifulSoup import BeautifulSoup
import urllib2
import re
import os
import sys
import multiprocessing
import time

def ChomikujPathToUtf(path):
    cnum = 0
    out = ''
    while cnum < len(path):
        if path[cnum]=='+': out += '%02x'%ord(' ')
        elif path[cnum]==':': out += '%02x'%ord('-')
        elif path[cnum]=='?': out += '%02x'%ord('_')
        elif path[cnum]=='*':
            out += path[cnum+1:cnum+3]
            cnum+=2
        else: out += '%02x'%ord(path[cnum])
        cnum+=1
    return out.decode('hex').decode('utf8')

class ChomikujMp3Downloader(multiprocessing.Process):
    def __init__(self,fq):
        multiprocessing.Process.__init__(self)
        self.fq = fq
    def run(self):
        while True:
            d = self.fq.get()
            if d is None: break
            self.do(d)
            self.fq.task_done()
        self.fq.task_done()
        return
    def do(self,d):
        (fullUrl,localBase,urlBase,urlType) = d
        if urlType == 'chomikuj_audio':
            m = re.match(r"^.*/(?P<name>.+),(?P<id>.+)\.(?P<ext>.+)\(audio\)$",fullUrl)
            if m:
                info = m.groupdict()
                download_url = 'http://chomikuj.pl/Audio.ashx?id=%s&type=2&tp=mp3'%info['id']
                name = ChomikujPathToUtf(info['name']) + '.'+info['ext']
                path = ChomikujPathToUtf(fullUrl[len(urlBase):])
                path = '/'.join((path.split('/')[:-1]))
                dstDir = '%s/%s/'%(localBase,path)
                dstDir = dstDir.replace('//','/')
                dstDir = dstDir.replace('//','/')
                dstFile = "%s%s"%(dstDir,name)
                print 'Pobieranie: %s'%name
                try: os.makedirs(dstDir)
                except Exception, e: pass
            	opener = urllib2.build_opener()
            	opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            	response = opener.open(download_url)
            	meta = response.info()
            	file_size = int(meta.getheaders("Content-Length")[0])
                data = response.read(file_size)
                dst = open(dstFile,'w')
                dst.write(data)
                dst.close()
                print 'Pobrano: %s'%name

class ChomikujDirectory:
    def __init__(self,url,local,files_queue=None):
        if files_queue==None:
            self.fq = multiprocessing.JoinableQueue()
            self.downloadManager = True
        else:
            self.fq = files_queue
            self.downloadManager = False
        self.url = url
        self.local = local
        self.downloaders_n = 4
    def download(self):
        urlsVisited = []
        urlsTodo = [self.url]
        downloaders = None
        urlsDownloaded = []
        if self.downloadManager:
            ds = [ ChomikujMp3Downloader(self.fq) for i in xrange(self.downloaders_n)]
            for d in ds:
                d.start()
        while True:
            if len(urlsTodo) == 0: break
            current = urlsTodo.pop(0)
            if urlsVisited.count(current) > 0: continue
            urlsVisited.append(current)
            html = urllib2.urlopen(current)
            soup = BeautifulSoup(html)
            for div in soup.findAll('div',attrs={'id':'folderContent'}):
                attrs = {k:v for (k,v) in div.attrs }
                if attrs.has_key('id') and attrs['id'] == 'folderContent':
                    for link in div.findAll('a',attrs={'href': re.compile("^.*\(audio\)$")}):
                        fullHref='http://chomikuj.pl'+link.get('href')
                        if urlsDownloaded.count(fullHref) > 0: continue
                        urlsDownloaded.append(fullHref)
                        d = (
                            fullHref,
                            self.local,
                            self.url,
                            'chomikuj_audio'
                        )
                        self.fq.put(d)
                    for subdiv in div.findAll('div',attrs={'id':'foldersList'}):
                        subattrs = {k:v for (k,v) in subdiv.attrs }
                        if subattrs.has_key('id') and subattrs['id'] == 'foldersList':
                            for dirLink in subdiv.findAll('a'):
                                href = 'http://chomikuj.pl'+dirLink.get('href')
                                urlsTodo.append(href)
        if self.downloadManager:
            for n in range(self.downloaders_n):
                self.fq.put(None)
            self.fq.join()


def main():
    url = sys.argv[-1]
    c = ChomikujDirectory(url,'.')
    c.download()

if __name__ == "__main__":
	main()
