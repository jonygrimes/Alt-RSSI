#!/usr/bin/python

# -*- coding: utf-8 -*-
# Written to work for Python 2.7
import csv, os, time, random, errno, re, argparse, urllib, abc
import sys, stat, signal, psutil, termios
from sys import stdout, stderr
from shutil import copy
from subprocess import Popen, call, PIPE
from signal import SIGINT, SIGTERM
from tempfile import mkdtemp
from random import shuffle
from shutil import rmtree
from timeit import default_timer as timer

# Library Functions
#-=-=-=-=-=-=-=-=-=-
    
# https://stackoverflow.com/questions/2520893/how-to-flush-the-input-stream-in-python
def flush_input(): # only works on LINUX
  termios.tcflush(sys.stdin, termios.TCIOFLUSH)
  stdout.flush()

def alarm():
  '''Makes 12 beeps by writing "\a" 12 times on the same line'''
  print "\n."
  for i in range(0,12):
    time.sleep(0.3)
    print "\x1b[1A.",  
    print "\r           \n",
    
class Sample:
  def __init__(self, rssi,dbm,time):
    self.clientRSSI,self.dbm,self.timestamp =rssi,dbm,time
    
class RunConfiguration:
  def CreateTempFolder(self):
    self.temp = mkdtemp(prefix='research')
    if not self.temp.endswith(os.sep):
      self.temp += os.sep
      
def rm(file):
  try:
    os.remove(file)
  except OSError:
    pass
    
def setAntennaStrength(dbm):  
  b = Popen(["ifconfig",args.interface,"up"], stdin=DN, stdout=DN, stderr=DN)
  c = Popen(["iwconfig",args.prom,"txpower",str(dbm)], stdin=DN, stdout=DN, stderr=DN)
  
def signal_handler(sig, frame):
  flush_input()
  print "Exited, successfully"
  sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

#~=~=~=~=~=~=~=~=~=~
# Main Functionality
#-=-=-=-=-=-=-=-=-=-
class RunEngine:
  def __init__(self, rc):
    self.RC = rc
    self.RC.RE = self

  def Start(self):
  
    # Create files if not present
    #-=-=-=-
    if not os.path.exists('files'): os.makedirs('files')
    if not os.path.exists('files/scan-total.csv'): 
      with open('files/scan-total.csv','w') as csvfile:
        w = csv.writer(csvfile,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
        w.writerow(["Set","Clock","antennaSTR","clientRSSI"])
    #~=~=~=~
    
    count=0
    x = sorted(set(args.dbm))

    while True:
    
      # Begin going through each Antenna Gain Strength
      for dbm in x:
        clientArray, current = [], []
        client = 999
        airo_pre = os.path.join('./', 'files','tmp',str(count),str(dbm),"empty")
        if not os.path.exists(airo_pre): os.makedirs(airo_pre)      
        
        print "Starting collection at: "+str(dbm)+" dbi (Iteration: "+str(count)+"):\n"
        setAntennaStrength(dbm)
        
        attempts=0
        while client == 999:
          if attempts>40:
            print "Please start wireless access point and connect a client to it"
          StationDump,b = Popen(["iw","dev","wlan1","station","dump"],stdout=PIPE).communicate()
        
          StationDump = re.split(' |\t',StationDump)
          
          if StationDump < 6:
            continue

          client = int(StationDump[6])*-1
          
        sp = Sample(client,dbm,timer()-start)
        flush_input()
        
        with open('files/scan-total.csv','a+') as csvf:
          w = csv.writer(csvf,delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
          w.writerow([str(count),sp.timestamp, sp.dbm, sp.clientRSSI])
        
        print "RSSI collection sample collected."
        
      count += 1
      

    flush_input()
    
#~=~=~=~=~=~=~=~=~=~

if __name__ == '__main__':

  # All of the parser stuff
  parser = argparse.ArgumentParser(description='ALT-RSSI: Alternating Strength to Detect MAC Spoof\n[Common Scan Script]\n\nThis program should be started with the wireless adapter of your choice started into monitor mode. Additionally, your monior station must be in a location where multiple disjoint RSSI pockets intersecting at differing levels of atenna gain strength.Additionally, please keep this python script running for both the learning and detection phase\n-=-=-=-=-=-=-\nNOTE: Although this is supposed to detect MAC spoofing attacks, to make testing easier all clients are considered to be the same device [will be changed before final release]',formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('-m','--client', metavar='00:11:22:33:44:55', help='This is the client\'s MAC address', type=str)
  parser.add_argument('-d','--dbm', metavar='# # #', help='All of the antenna gain strengths scaned', type=int, nargs='+',required=True)
  parser.add_argument('-i','--interface', dest='interface', metavar='wlan0', help='raw (un-promiscuous) interface', type=str, default="wlan1")

  global args, DN, start
  args = parser.parse_args()
  DN = open(os.devnull, 'w')
  start = timer()
  
  RC = RunConfiguration()
  RunEngine(RC).Start()

