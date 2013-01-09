#!/usr/bin/python2
# -*- coding: utf-8 -*-

'''
    This file is part of KSP Groundtracker.

    KSP Groundtracker is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.

    KSP Groundtracker is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with KSP Groundtracker.  If not, see <http://www.gnu.org/licenses/>.
'''

import SimpleHTTPServer,SocketServer,cgi,zipfile,sys,time
import rarfile,track,sync

PORT = 8000

class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        logging.error(self.headers)
        #SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
        self.send_response(200,"OK")
        self.send_header("Content-type","text/html")
        self.end_headers()

        f = open("groundtrack.html","r")
        self.wfile.write(f.read())
        f.close()
        print ("Sent main page.")

    def do_POST(self):
        #logging.error(self.headers)
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })
        #for item in form.list:
        #    print "ITEM"
        #    print dir(item)
        #SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
        v=form['ifile'].value
        fn=form['ifile'].filename 
        if fn[-3:].lower() == "zip":
            f=open('temp.zip','wb')
            f.write(v)
            f.close()
            z = zipfile.ZipFile("temp.zip","r")
            members = z.namelist()
            print "MEMBERS zip:",members
            if len(members) != 1:
                self.wfile.write("Failed to process zip file. More than one file?")
                sys.exit(1)
            if "/" in members[0]:
                self.wfile.write("Failed to process zip file.")
                sys.exit(1)
            z.extractall(path="./tmp")
            datafile = "./tmp/%s"%members[0]
        elif fn[-3:].lower() == "rar":
            f=open('temp.rar','wb')
            f.write(v)
            f.close()
            z = rarfile.RarFile("temp.rar","r")
            members = z.namelist()
            print "MEMBERS rar:",members
            if len(members) != 1:
                self.wfile.write("Failed to process rar file.")
                sys.exit(1)
            if "/" in members[0]:
                self.wfile.write("Failed to process rar file.")
                sys.exit(1)
            z.extractall(path="./tmp")
            datafile = "./tmp/%s"%members[0]
        else:
            print fn
            print fn[-3:]
            print "???"
        print "Handle file:",datafile
        if form["filetype"].value == "track":
            print "Handle track"
            t = track.Plotter()
            plt = t.plot_track(datafile)
            fname = "./tmp/plot_%f.svg"%(time.time())
            plt.savefig(fname,dpi=100)
            
        else:
            print "Handle persistence"
            p = sync.Persistent(datafile)
            snapshot = p.create_snapshot()
            self.wfile.write("Persistent.sfs file is not yet supported")
            
        self.send_response(200,"OK")
        self.send_header("Content-type","text/html")
        self.end_headers()
        
        self.wfile.write("OKAY")

Handler = ServerHandler

httpd = SocketServer.TCPServer(("", PORT), Handler)

print "serving at port", PORT
httpd.serve_forever()
