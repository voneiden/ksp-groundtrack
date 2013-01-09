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

import SimpleHTTPServer,SocketServer,cgi,zipfile,sys,time,re
import rarfile,track,persistant

PORT = 8000

class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        print ("REQ:"+self.path)
        if self.path in ["/","/jquery.js"]:
            if self.path == "/":
                self.path =  "/groundtrack.html"
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
        else:
            if re.match("/tmp/\w*\.[0-9]*\.svg$",self.path):
                
                try:
                    f = open(self.path[1:],"rb")
                except:
                    self.send404()
                    return
                self.send_response(200,"OK")
                self.send_header("Content-type","image/svg+xml")
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            self.send404()
            
    def send404(self):
        self.send_response(404,"NOT FOUND")
        self.send_header("Content-type","text/plain")
        self.end_headers()
        self.wfile.write("This is not the file you are looking for..")

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

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
            self.send404()
            return
        print "Handle file:",datafile
        if form["predict"].value == "predict":
            predict = True
        else:
            predict = False
        if form["filetype"].value == "track":
            print "Handle track"
            t = track.Track()
            plt = t.plot_track(t.read_track(datafile),predict)
            fname = "./tmp/plot_%f.svg"%(time.time())
            plt.savefig(fname,dpi=100)
            
        else:
            print "Handle persistant"
            p = sync.Persistent(datafile)
            t = track.Track()
            plt = t.plot_track(p.create_snapshot(),True)
            fname = "./tmp/plot_%f.svg"%(time.time())
            plt.savefig(fname,dpi=100)

          
        self.send_response(303,"See Other")
        self.send_header("Location",fname[2:])
        self.end_headers()
        
        #self.wfile.write("OKAY")

Handler = ServerHandler

httpd = SocketServer.TCPServer(("", PORT), Handler)

print "serving at port", PORT
httpd.serve_forever()
