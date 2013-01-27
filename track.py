#!/usr/bin/python2
# -*- coding: utf-8 -*-
from math import radians
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


import PyKEP,sys,mpl_toolkits.basemap, random
from math import radians, degrees
import numpy as np
import matplotlib as mpl
from matplotlib.ticker import FormatStrFormatter
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
#from PyKEP.orbit_plots import plot_planet, plot_lambert, plot_kepler



class Ship:
    def __init__(self,pid,name):
        self.pid = pid
        self.name = name
        self.datapoints = {}
    def add_data(self,UT,T,DATA):
        UT = float(UT)
        if T == "LND" or T == "FLY":
            longitude = float(DATA[0]) + 90 # <- Sort this out
            latitude = float(DATA[1])
            if longitude > 180:
                longitude -= 360
            self.datapoints[UT] = [longitude,latitude]
        elif T == "KEP":
            epoch = float(DATA[0]) / 60.0 / 60.0 / 24.0
            sma = float(DATA[1])
            e = float(DATA[2])
            inc = np.radians(float(DATA[3]))
            lan = np.radians(float(DATA[4]))
            w = np.radians(float(DATA[5]))
            mep = float(DATA[6])
            self.datapoints[UT] = [epoch,sma,e,inc,lan,w,mep]
            
    def clean_data(self):
        new_datapoints = {}
        keys = self.datapoints.keys()
        keys.sort()
        self.min = keys[0]
        #self.max = keys[1]
        print "Datapoints",len(self.datapoints)
        for i,key in enumerate(keys):
            if i == 0: 
                new_datapoints[key] = self.datapoints[key]
                continue
            this = self.datapoints[key]
            last = self.datapoints[keys[i-1]]
            if this == last:
                print "Skipping stuff because its the same"
                continue
            
            new_datapoints[key] = self.datapoints[key]
        self.datapoints = new_datapoints
        print "New datapoints",len(self.datapoints)


class Track:
    def read_track(self,fname):
                
        shippids = {}
        biggestUT = 0
        
        f=open(fname,'rb')
        for line in f.readlines():
            line = line.strip()
            if len(line) == 0: continue
            tok = line.split('\t')
            print tok
            if tok[0] == "VESSEL":
                shippids[tok[1]] = Ship(tok[1],tok[2])
                
            else:
                try: UT = float(tok[0]) / 60 / 60 / 24
                except:
                    print "Invalid line"
                    continue
                T = tok[1]
                PID = tok[2]
                DATA = tok[3:]
                #DATA[0] = float(DATA[0]) #epoch
                #DATA[1] = float(DATA[1]) #a
                #DATA[2] = float(DATA[2]) #e
                #DATA[3] = radians(float(DATA[3])) #i
                #DATA[4] = radians(float(DATA[4])) #W
                #DATA[5] = radians(float(DATA[5])) #w
                #DATA[6] = float(DATA[6]) #M0

                shippids[PID].add_data(UT,T,DATA)
                if UT > biggestUT:
                    biggestUT = UT
            
        f.close()

        for pid,ship in shippids.items():
            print "Cleaning pid",pid
            ship.clean_data()
            print "Final orbit data"
            keys = ship.datapoints.keys()
            keys.sort()
            for key in keys:
                print key,ship.datapoints[key]
            #print ship.datapoints
            
        UT = biggestUT
        print "Final Epoch",UT

        for ship in shippids.values():
            if ship.name == "KSS 1e" or ship.name == "KomSat 4" or ship.name == "KSS 1 Probe":
                del shippids[ship.pid]

        return [UT,shippids]

    def plot_track(self,data,predict=True,longplot=False):
        UT = data[0]
        shippids = data[1]
        
        fig = plt.figure(figsize=(20,10))
        kmap = mpl_toolkits.basemap.Basemap(rsphere=600000,celestial=True,resolution=None)
        im = plt.imread("Kerbin_elevation.png")
        #implot = plt.imshow(im)
        kmap.imshow(im,origin="upper")


        #UT = float(ss["UT"]) / 60 / 60 / 24
        #ships = ss["VESSELS"]
        #colors = ["red","green","white","cyan","orange","yellow","purple","brown"]
        nearest=lambda a,l:min(l,key=lambda x:abs(x-a)) # Thanks stackexchange
        if longplot:
            steps = 720 #Minutes
        else:
            steps = 30 #Minutes
        trackTime = steps/60/24 #  30 minutes
        stepTime = 1.0/60.0/24.0 # 1 minute
        reserved = []
        for ship in shippids.values():
            last_rascension = None
            last_declination = None
            if "debris" in ship.name.lower():
                continue
            XY = []
            for i in xrange(steps):
                stepEpoch = UT - i*stepTime
                if stepEpoch<ship.min and not predict: #TODO: predictorbits
                    stepEpoch = ship.min #This is to ensure that no orbits are drawn which have unsure stuff
                nt = nearest(stepEpoch,ship.datapoints.keys())
                print "Epoch ",stepEpoch,"using datapoint",nt
                dp = ship.datapoints[nt]
                
                if len(dp) == 2:
                    XY.append([dp[0],dp[1]])
                elif len(dp) == 7:
                    E = PyKEP.epoch(dp[0])
                    KepShip = PyKEP.planet(E,[dp[1],dp[2],dp[3],dp[4],dp[5],dp[6]],3531600000000,1,1,1)
                    r,v = KepShip.eph(PyKEP.epoch(stepEpoch))
                    r = np.array(r)
                    theta = -0.000290888209 * stepEpoch * 60 * 60 * 24
                    rmatrix = np.array([[np.cos(theta),np.sin(theta),0],[-np.sin(theta),np.cos(theta),0],[0,0,1]])
                    rr=np.dot(r,rmatrix)
                    ur = rr / np.linalg.norm(rr)
                    declination = np.arcsin(ur[2])
                    if ur[1] > 0:
                        rascension = np.degrees(np.arccos(ur[0] / np.cos(declination)))
                    elif ur[1] <= 0:
                        rascension = - np.degrees(np.arccos(ur[0]/ np.cos(declination)))
                       # print "360-",np.degrees(np.arccos(ur[0]/ np.cos(declination)))
                    declination = np.degrees(declination)

                    # Insert NaN if crossing 180 or -180
                    if last_rascension != None:
                        dif = rascension - last_rascension
                        if dif > 180 or dif < -180:
                            if dif < -180: # Going from 180 to -180
                                k = (declination - last_declination) / ((rascension - 180) + (180-last_rascension))
                                d = (180 - last_rascension)*k + last_declination
                                XY.append([180,d])
                                XY.append([np.NaN,np.NaN])
                                XY.append([-180,d])
                            else: # Going from -180 to 180
                                k = (declination - last_declination) / ((180-rascension) + (last_rascension-180))
                                d = (last_rascension-180)*k + last_declination
                                XY.append([-180,d])
                                XY.append([np.NaN,np.NaN])
                                XY.append([180,d])
                                
                            XY.append([np.NaN,np.NaN]) #FLIP
                    last_rascension = rascension
                    last_declination = declination
                    XY.append([rascension,declination])
                    
                else:
                    print "Error"
                    sys.exit(1)
            
            lastx = None
            lasty = None
            #color = random.choice(colors)
            r = random.randint(100,255) / 255.0
            g = random.randint(100,255)/ 255.0
            b = random.randint(100,255)/ 255.0
            color = (r,g,b)
            #colors.remove(color)
            alphafade = 1.0 / len(XY)
            for i,point in enumerate(XY):
                if i == 0:
                    lastx = point[0]
                    lasty = point[1]
                    continue
                    
                x = point[0]
                y = point[1]
                if lastx and lasty:
                    kmap.plot([x,lastx],[y,lasty],color=color,alpha=1-i*alphafade)
                lastx = x
                lasty = y
                    
            kmap.plot(XY[0][0],XY[0][1],marker="x",markersize=10,color=color)
            kmap.plot(XY[0][0],XY[0][1],marker="+",markersize=10,color=color)
            
            if XY[0][0] > 0:
                mx = -4*len(ship.name)
            else:
                mx = 2*len(ship.name)
            if XY[0][1] >= 0:
                my = -20+XY[0][1]
                while int(my/5) in reserved:
                    my-=5
                reserved.append(int(my/5))
            elif XY[0][1] < 0:
                my = 20+XY[0][1]
                while int(my/5) in reserved:
                    my+=5
                reserved.append(int(my/5))
          
            print "ship:",ship.name,mx,my
            print "reserved",reserved
            plt.annotate(ship.name,xy=(XY[0][0],XY[0][1]), xycoords="data",xytext=(mx+XY[0][0],my),textcoords="data",color=color,arrowprops=dict(arrowstyle="->",color=color))
            
            
            
        days = int(UT) 
        years = days / 365 + 1
        days %= 365
        days += 1

        plt.title("Kerbin satellite ground track - Year %i, Day %i"%(years,days))
        print ("Track.py completed succesfully")
        return plt
        #plt.show()


