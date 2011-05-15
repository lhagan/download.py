#!/usr/bin/env python

"""
download.py: simple HTTP file downloads with libcurl and Python
by Luke D. Hagan <lukehagan.com>

Revision History:
0.1.0 - 2011-05-15 - initial release

This is free and unencumbered software released into the public domain.
See UNLICENSE.txt or unlicense.org/ for more information.

"""

# TODO: consider using libcurl multi interface
import os
import pycurl
import sys
import time
import urllib2
from threading import Thread

class Download(Thread):
    def __init__(self, url, path, cookies=False, useragent=False):
        super(Download, self).__init__()
        self.url = url
        self.path = path
        self.useragent = useragent
        self.cookies = cookies
        self.downloaded = 0
        
        self.progress = { 'downloaded': 0, 'total': 0, 'percent': 0 }
        self.stop = False
        self.filename = ""

    def run(self):
        
        #
        # first, get the actual URL
        #
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self.url)
        c.setopt(pycurl.FOLLOWLOCATION, 1)
        c.setopt(pycurl.MAXREDIRS, 5)
        c.setopt(pycurl.NOBODY, 1)
        if self.useragent:
            c.setopt(pycurl.USERAGENT, self.useragent)
        
        # add cookies, if available
        if self.cookies:
            c.setopt(pycurl.COOKIE, self.cookies)
        c.perform()
        realurl = c.getinfo(pycurl.EFFECTIVE_URL)
        
        self.filename = realurl.split("/")[-1].strip()
        
        #
        # now start the download
        #

        # configure pycurl
        c = pycurl.Curl()
        c.setopt(pycurl.URL, realurl)
        c.setopt(pycurl.FOLLOWLOCATION, 0)
        c.setopt(pycurl.NOPROGRESS, 0)
        c.setopt(pycurl.PROGRESSFUNCTION, self.getProgress)
        if self.useragent:
            c.setopt(pycurl.USERAGENT, self.useragent)
        
        # configure pycurl output file
        if self.path == False:
            self.path = os.getcwd()
        filepath = os.path.join(self.path, self.filename)
            
        if os.path.exists(filepath):
            f = open(filepath, "ab")
            self.downloaded = os.path.getsize(filepath)
            c.setopt(pycurl.RESUME_FROM, self.downloaded)
        else:
            f = open(filepath, "wb")
        c.setopt(pycurl.WRITEDATA, f)
        
        # add cookies, if available
        if self.cookies:
            c.setopt(pycurl.COOKIE, self.cookies)
    
        # download file
        c.perform()
        c.close()
        
    def getProgress(self, total, existing, upload_t, upload_d):
        if total and existing:
            self.progress['downloaded'] = float(existing + self.downloaded)
            self.progress['total'] = float(total + self.downloaded)
            self.progress['percent'] = ( self.progress['downloaded'] / self.progress['total']) * 100

        if self.stop:
            # TODO: fix resulting exception
            return 1
        
    def cancel(self):
        # sets the boolean to stop the thread.
        self.stop = True
        
def main():
    from optparse import OptionParser
    
    parser = OptionParser(usage="%prog [options] <url>")
    parser.add_option(  "-p", "--path", default=False, dest="path", help="download file to PATH", metavar="PATH")
    parser.add_option(  "-c", "--cookies", default=False, dest="cookies", help="specify cookie(s)", metavar="COOKIES")
    opts, args = parser.parse_args()

    if len(args) == 0:
        parser.error("No url supplied")
    
    for url in args:
        print("Downloading: %s" % url)
        if opts.path:
            print("to: %s" % opts.path)
        else:
            print("to current directory")
        d = Download(url, opts.path, opts.cookies)
        d.start()

        while 1:
            try:
                progress = d.progress['percent']
                print("%.2f percent | %.2f of %.2f" % (progress, d.progress['downloaded'], d.progress['total']))
                if progress == 100:
                    print("")
                    print("Download complete: %s" % d.filename)
                    break
                time.sleep(1)

            # tell thread to terminate on keyboard interrupt,
            # otherwise the process has to be killed manually
            except KeyboardInterrupt:
                d.cancel()
                break

            except:
                raise
            
if __name__ == "__main__":
    main()