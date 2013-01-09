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
import track

class Node:
    def __init__(self,name,parent=None):
        self.name = name
        self.parent = parent
        if self.parent:
            self.depth = self.parent.depth + 1
            self.parent.kids.append(self)
        else:
            self.depth = 0
        self.kids = []

class Vessel(Node):
    def __init__(self,name,parent=None):
        Node.__init__(self,name,parent)
        
        
class Key:
    def __init__(self,parent,key,value):
        self.parent = parent
        self.key = key.strip()
        self.value = value.strip()
        #self.parent.kids.append(self)
        setattr(self.parent,self.key,self.value)
        

class Persistent:
    def __init__(self,fname):
        self.vessels = []
        f = open(fname,"r")
        nodestack = []
        lastvalue = None
        root = None

        for line in f.readlines():
            stripped = line.strip()
            if "=" in stripped:
                x=stripped.split('=',1)
                key = Key(nodestack[-1],x[0],x[1])
                #print "."*key.parent.depth + ".KEY:"+key.key
            elif stripped == "{":
                if len(nodestack) == 0:
                    self.root = Node(lastvalue)
                    nodestack.append(self.root)
                    print "ROOT:"+self.root.name
                else:
                    node=Node(lastvalue,nodestack[-1])
                    nodestack.append(node)
                    #print "."*node.depth + "NODE:" + node.name
                    if lastvalue == "VESSEL":
                        self.vessels.append(node)
                    
                    
            elif stripped == "}":
                nodestack.pop()
                
            else:
                lastvalue = stripped

        print "Done."
        if len(nodestack) != 0:
            print "Problems, nodestack is not zero:",len(nodestack)
    def create_snapshot(self):
        for kid in self.root.kids:
            if kid.name == "FLIGHTSTATE":
                UT = float(kid.UT) / 60.0 / 60.0 / 24.0
                break
        snapshot = {}
        
        print "Universal time:",UT
        shippids = {}
        for vessel in self.vessels:
            if "Debris" in vessel.name:
                continue

            if vessel.sit == "ORBITING":
                print "Vessel",vessel.pid,vessel.sit
                for kid in vessel.kids:
                    if kid.name == "ORBIT":
                        if kid.REF == "1":
                            a = kid.SMA
                            e = kid.ECC
                            i = kid.INC
                            W = kid.LAN
                            w = kid.LPE
                            M = kid.MNA
                            E = kid.EPH
                            shippids[vessel.pid] = track.Ship(vessel.pid,vessel.name)
                            shippids[vessel.pid].add_data(UT,"KEP",[E,a,e,i,W,w,M])
                            shippids[vessel.pid].clean_data()
                            
                        break
            elif vessel.sit == "LANDED":
                shippids[vessel.pid] = track.Ship(vessel.pid,vessel.name)
                shippids[vessel.pid].add_data(UT,"LND",[vessel.lon,vessel.lat])
                shippids[vessel.pid].clean_data()
        return [UT,shippids]
        
if __name__ == '__main__':
    print "Parsing"
    p = Persistent()
    print "Parsed"
    snapshot = p.create_snapshot()
    import pickle
    f=open("output.pickle",'wb')
    pickle.dump(snapshot,f)
    f.close()
    print"Danke"
                        
                    
        #for kid in vessel.kids:
            
