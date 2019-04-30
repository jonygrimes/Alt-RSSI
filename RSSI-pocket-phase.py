#!/usr/bin/python

# -*- coding: utf-8 -*-
import csv, os, time, random, errno, re, argparse, urllib, abc
from sys import argv, stdout
from shutil import copy
from subprocess import Popen, call, PIPE
from signal import SIGINT, SIGTERM
from tempfile import mkdtemp
import signal
import sys
# from playsound import playsound
import psutil

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()
    
def flush_input():
    try:
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    except ImportError:
        import sys, termios    #for linux/unix
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
        
def alarm():
  print "\n\a."
  for i in range(0,12):
    time.sleep(0.3)
    print "\x1b[1A.\a",
    print "\r           \n",
    

        
ifaceNonMon = "wlan0"
iface = ifaceNonMon


#globalbssid = "C0:4A:00:44:75:04"
globalbssid = "8C:3B:AD:42:2E:4E"
globalchannel = "1"
DN = open(os.devnull, 'w')

def scanAndWait(file,current,airo_pre):
  count = 0
  # rm(file)
  while True:
    if os.path.exists(file):
      if len(open(file).readlines()) >= 4:
        print "*"
        stdout.flush()
        return file
      else:
        print "+",
        count = 50
        stdout.flush()
        time.sleep(1)
    else:
      print ".",
      count += 1
      stdout.flush()
      time.sleep(1)
    if count == 45:
      alarm()
      for i in range(0,12):
        time.sleep(0.3)
        print ".\a",
      raw_input("Please unplug the wireless interface [any key to continue]\a\a:")
      
      time.sleep(10)
      k = Popen(["rfkill","unblock","wifi;", "sudo","rfkill","unblock","all;","ifconfig",ifaceNonMon,"up"], stdout=DN, stderr=DN)
      l = Popen(["airmon-ng","start",ifaceNonMon], stdout=DN, stderr=DN)
      time.sleep(5)
      a = Popen(["ifconfig",iface,"down"], stdout=DN, stderr=DN)
      b = Popen(["iw","reg", "set", "b0"], stdout=DN, stderr=DN)
      c = Popen(["ifconfig",iface,"up"], stdout=DN, stderr=DN) 
      if not os.path.exists(airo_pre): os.makedirs(airo_pre)
      current += 1
      file = airo_pre + '-'+"%02d" % (current,) +'.csv'
      d = Popen(['airodump-ng', '-a','--write-interval', '1', '--bssid', globalbssid, '-c', globalchannel, '-w', airo_pre, iface], stdout=DN, stderr=DN)
      e = Popen(["iwconfig",iface,"txpower",str(rssi)], stdout=DN, stderr=DN)
      count = 0
      return file


class Target:
  def __init__(self, bssid, power, data, channel, encryption, ssid):
    self.bssid, self.power, self.data, self.channel, self.encryption,self.ssid,self.key  = bssid, power, data, channel, encryption, ssid, ''

class Client:
  def __init__(self, bssid, station, power):
    self.bssid, self.station, self.power = bssid, station, power

class Spot:
  def __init__(self, x,y,bssidArray,clientArray,rssi):
    self.x, self.y, self.bssidArray, self.clientArray, self.bssidRSSI, self.clientRSSI,self.rssi =x,y,bssidArray,clientArray, (sum(bssidArray)/len(bssidArray)), (sum(clientArray)/len(clientArray)),rssi

class RunConfiguration:
  def CreateTempFolder(self):
    self.temp = mkdtemp(prefix='research')
    if not self.temp.endswith(os.sep):
      self.temp += os.sep

class RunEngine:
  def __init__(self, rc):
    self.RC = rc
    self.RC.RE = self

  def Start(self):
    bssidArray = []
    clientArray = []
    spotArray = []
    access_point = 0
    clientPowers = dict()
    airo_pre=""
    if not os.path.exists('alt-rssi-t.csv'): 
      with open('alt-rssi-t.csv','w') as csvfile:
        w = csv.writer(csvfile,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
        w.writerow(["x, Y, RSSI, bssidArray, ClientArray, AverageBssidRSSI, AverageClientRSSI"])
        for sp in spotArray:
          w.writerow([sp.x,sp.y,sp.rssi,str(sp.bssidArray),str(sp.clientArray), sp.bssidRSSI,sp.clientRSSI])
    
    print "Hi!\a",
    
    while True:
      try:
        stdout.flush()
        flush_input()
        x=int(raw_input("\nx: "))
        y=int(raw_input("y: "))
      except:
        with open('alt-rssi-t-backup.csv','a+') as csvfile:
          w = csv.writer(csvfile,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
          w.writerow(["x, Y, RSSI, bssidArray, ClientArray, AverageBssidRSSI, AverageClientRSSI"])
          for sp in spotArray:
            w.writerow([sp.x,sp.y,sp.rssi,str(sp.bssidArray),str(sp.clientArray), sp.bssidRSSI,sp.clientRSSI])
      print "\nX:" + str(x) + ", Y:"+str(y) +"\n"

      time.sleep(10)
      print 'MoveToSeat:\a'
      
      for rssi in [0,5,10,15,20,25,30]:
        current = 1
        airo_pre = os.path.join('./', 'research',str(x),str(y),str(rssi),"empty")
        if not os.path.exists(airo_pre): os.makedirs(airo_pre)
        file = airo_pre + '-'+"%02d" % (current,) +'.csv'       
        
        a = Popen(["ifconfig",iface,"down"], stdout=DN, stderr=DN)
        b = Popen(["iw","reg", "set", "b0"], stdout=DN, stderr=DN)
        c = Popen(["ifconfig",iface,"up"], stdout=DN, stderr=DN) 
        bssidArray = []
        clientArray = []
        access_point = 0
        clientPowers = dict()
        
      
        print "Starting collection at: "+str(rssi)+" dbi:\n"
        d = Popen(['airodump-ng', '-a','--write-interval', '1', '--bssid', globalbssid, '-c', globalchannel, '-w', airo_pre, iface], stdout=DN, stderr=DN)
        e = Popen(["iwconfig",iface,"txpower",str(rssi)], stdout=DN, stderr=DN)
        
        file = scanAndWait(file,current,airo_pre)

        with open(file+'alt-rssi.csv','w') as csvfile:
           w = csv.writer(csvfile,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
           w.writerow(["x, Y, RSSI, bssidArray, ClientArray, AverageBssidRSSI, AverageClientRSSI"])
        
        while len(clientArray)< 5:
          
          time.sleep(1)
          if len(clientArray) == 0:
            c = Popen(["ifconfig",iface,"up"], stdout=DN, stderr=DN) 
            print ",",
          else: 
            print "Client: " + str(len(clientArray)) + "  ",
          if not os.path.exists(file): 
            # kill(p.pid)
            alarm()
            print "OH NO!!\n-=-=-=-=-=-=-=-=-=-=-\n\a"
            
          target, clients = Target("", "", "","", "", ""), []
          hit_clients = False
          with open(file, 'rb') as csvfile:
            targetreader = csv.reader((line.replace('\0', '') for line in csvfile), delimiter=',')
            for row in targetreader:
              if len(row) < 2: continue
              if (row[0] == globalbssid):
                access_point = int(row[8])
                print "Access Point: " + str(access_point)
                bssidArray+=[(access_point)]
                continue
              if not hit_clients:
                if row[0].strip() == 'Station MAC':
                  hit_clients = True
                  continue
                if len(row) < 14 or row[0].strip() == 'BSSID': continue
                power = int(row[8].strip())

                if power < 0: power += 100
                target = Target(row[0].strip(), power, row[10].strip(), row[3].strip(), row[5].strip(), row[13].strip()[:int(row[12].strip())])
              else:
                if len(row) >= 6 and re.sub(r'[^a-zA-Z0-9:]', '', row[5].strip()) != 'notassociated':
                  clients.append(Client(re.sub(r'[^a-zA-Z0-9:]', '', row[0].strip()), re.sub(r'[^a-zA-Z0-9:]', '', row[5].strip()), row[3].strip()))
                  clientPowers[str(re.sub(r'[^a-zA-Z0-9:]', '', row[0].strip()))] = int(row[3].strip())
                  print "-" + str(re.sub(r'[^a-zA-Z0-9:]', '', row[0].strip())) + " : " + str(row[3].strip())
                  clientArray+=[(int(row[3].strip()))]
                                   
        # playsound(str(rssi)+'.m4a', False);
        # kill(p.pid)
        # kill(d.pid)
        sp = Spot(x,y,bssidArray,clientArray,rssi)
        print "SP: " + str(sp.x) + ":" + str(sp.y) + ":" + str(sp.bssidArray) + ":" + str(sp.clientArray) + ":" + str(sp.bssidRSSI) + ":" + str(sp.clientRSSI) + ":" +str(rssi) +"\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n"
        spotArray+=[sp]
        stdout.flush()
        
        with open(airo_pre+'alt-rssi.csv','a+') as csvf:
          w = csv.writer(csvf,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
          w.writerow(["x, Y, RSSI, bssidArray, ClientArray, AverageBssidRSSI, AverageClientRSSI"])
          w.writerow([sp.x,sp.y,sp.rssi,str(sp.bssidArray),str(sp.clientArray), sp.bssidRSSI,sp.clientRSSI])

        with open('alt-rssi-t.csv','a+') as csvfile:
          w = csv.writer(csvfile,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
          w.writerow([sp.x,sp.y,sp.rssi,str(sp.bssidArray),str(sp.clientArray), sp.bssidRSSI,sp.clientRSSI])
          
        print "One pass through complete.\a"
      
      alarm()
      stdout.flush()
      flush_input()
      print "Need input:\n"
      
      #try:      
      #  over=raw_input("end? [Y/N]")
      #except:
      #  over="Y"
      over = "y"
    
      if over == "Y" or over == "y" or over == "Yes" or over == "yes":
        time.sleep(1)
        for i in range(0,3):
          time.sleep(0.3)
          print "       \r.\a"
        print("\rSee you next time             \n\a")
        stdout.flush()
        flush_input()
        #with open('alt-rssi-t.csv','a+') as csvfile:
        #  w = csv.writer(csvfile,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
          # w.writerow(["x, Y, RSSI, bssidArray, ClientArray, AverageBssidRSSI, AverageClientRSSI"])
        #  for sp in spotArray:
        #    w.writerow([sp.x,sp.y,sp.rssi,str(sp.bssidArray),str(sp.clientArray), sp.bssidRSSI,sp.clientRSSI])
        break
        
    stdout.flush()
    sys.exit()

def rm(file):
  try:
    os.remove(file)
  except OSError:
    pass

if __name__ == '__main__':
  #call(['airmon-ng', 'start', iface], stdout=DN, stderr=DN)
  RC = RunConfiguration()
  RunEngine(RC).Start()

