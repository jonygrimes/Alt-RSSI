#!/usr/bin/python

# -*- coding: utf-8 -*-
# Written to work for Python 2.7
import csv, os, time, random, errno, re, argparse, urllib, abc
import sys
import stat
from sys import argv, stdout
from shutil import copy
from subprocess import Popen, call, PIPE
from signal import SIGINT, SIGTERM
from tempfile import mkdtemp
from random import shuffle
from shutil import rmtree
import signal
import psutil

# https://stackoverflow.com/questions/4789837/how-to-terminate-a-python-subprocess-launched-with-shell-true
def kill(proc_pid):
  process = psutil.Process(proc_pid)
  for proc in process.children(recursive=True):
    proc.kill()
  process.kill()
    
# https://stackoverflow.com/questions/2520893/how-to-flush-the-input-stream-in-python
def flush_input():
  try:
    import msvcrt
    while msvcrt.kbhit():
      msvcrt.getch()
  except ImportError:
    import sys, termios    #for linux/unix
    termios.tcflush(sys.stdin, termios.TCIOFLUSH)

def alarm():
  '''Makes 12 beeps by writing "\a" 12 times on the same line'''
  print "\n."
  for i in range(0,12):
    time.sleep(0.3)
    print "\x1b[1A.",  
    print "\r           \n",
    
# https://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail
def tail(file, lines=30, _buffer=4098):
  f = open(file, "r");
  """Tail a file and get X lines from the end"""
  # place holder for the lines found
  lines_found = []

  # block counter will be multiplied by buffer
  # to get the block size from the end
  block_counter = -1

  # loop until we find X lines
  while len(lines_found) <= lines:
    try:
      f.seek(block_counter * _buffer, os.SEEK_END)
    except IOError:  # either file is too small, or too many lines requested
      f.seek(0)
      lines_found = f.readlines()
      break

    lines_found = f.readlines()

    # decrement the block counter to get the
    # next X bytes
    block_counter -= 1
  
  try:
    write = open(file, "w");
    if len(lines_found[-lines:]) > 30:
      write.write("'antennaSTR','clientRSSI','bssidRSSI','bssidArray','clientArray'\n")
    for i in lines_found[-lines:]:
      write.write(i)
  except:
    alarm()
    print "ERROR HAPPENED WHEN SAVING FILE!!"

  return lines_found[-lines:]
    

ifaceNonMon = "wlan0"
iface = ifaceNonMon

globalbssid = "[REDACTED]"
globalchannel = "1"
DN = open(os.devnull, 'w')

def del_evenReadonly(action, name, exc):
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)

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
        print ".",
      raw_input("Please unplug the wireless interface.\nAfter this, please press any key to continue]:")
      
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
  def __init__(self, bssidArray,clientArray,rssi):
    self.bssidArray, self.clientArray, self.bssidRSSI, self.clientRSSI,self.rssi =bssidArray,clientArray, (sum(bssidArray)/len(bssidArray)), (sum(clientArray)/len(clientArray)),rssi

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
    if not os.path.exists('files'): os.makedirs('files')
        
    if not os.path.exists('files/scan-30.csv'): 
      with open('files/scan-30.csv','w') as csvfile:
        w = csv.writer(csvfile,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
        w.writerow(["antennaSTR","clientRSSI", "bssidRSSI", "bssidArray","clientArray"])
    
    print "Hello, this program should be started with the wireless adapter of your choice started into monitor mode. Additionally, your monior station must be in a location where multiple disjoint RSSI pockets intersecting at differing levels of atenna gain strength.Additionally, please keep this python script running for both the learning and detection phase\n",
    count=0
    
    try:
      while True:
        
        # Randomize order of list to increase difficulty of evasion
        x = [0,5,10,15,20,25,30]
        shuffle(x)
        
        # Begin going through each Antenna Gain Strength
        for rssi in x:
          current = 1
          airo_pre = os.path.join('./', 'files','tmp',str(count),str(rssi),"empty")
          if not os.path.exists(airo_pre): os.makedirs(airo_pre)
          file = airo_pre + '-'+"%02d" % (current,) +'.csv'       
          
          a = Popen(["ifconfig",iface,"down"], stdout=DN, stderr=DN)
          b = Popen(["iw","reg", "set", "b0"], stdout=DN, stderr=DN)
          c = Popen(["ifconfig",iface,"up"], stdout=DN, stderr=DN) 
          bssidArray = []
          clientArray = []
          access_point = 0
          clientPowers = dict()
        
          print "Starting collection at: "+str(rssi)+" dbi (Iteration: "+str(count)+"):\n"
          d = Popen(['airodump-ng', '-a','--write-interval', '1', '--bssid', globalbssid, '-c', globalchannel, '-w', airo_pre, iface], stdout=DN, stderr=DN)
          e = Popen(["iwconfig",iface,"txpower",str(rssi)], stdout=DN, stderr=DN)
          
          file = scanAndWait(file,current,airo_pre)
          
          while len(clientArray)< 2:
            time.sleep(1)
            if len(clientArray) == 0:
              c = Popen(["ifconfig",iface,"up"], stdout=DN, stderr=DN) 

            if not os.path.exists(file): 
              print "OH NO!!\n-=-=-=-=-=-=-=-=-=-=-\n"
              
            target, clients = Target("", "", "","", "", ""), []
            hit_clients = False
            with open(file, 'rb') as csvfile:
              targetreader = csv.reader((line.replace('\0', '') for line in csvfile), delimiter=',')
              for row in targetreader:
                if len(row) < 2: continue
                if (row[0] == globalbssid):
                  access_point = int(row[8])
                  # print "Access Point: " + str(access_point)
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
                    clientArray+=[(int(row[3].strip()))]
                                     
          sp = Spot(bssidArray,clientArray,rssi/5 + 1)
          stdout.flush()
          
          # Less efficient to keep two seperate files, but this is to ensure that
          #   all the data is kept. (Data Retainment Ensurance)
          with open('files/scan-30.csv','a+') as csvf:
            w = csv.writer(csvf,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
            w.writerow([sp.rssi, sp.clientRSSI, sp.bssidRSSI, str(sp.bssidArray),str(sp.clientArray)])
            
          
          # Keep only the last 30 lines of this file
          tail('files/scan-30.csv')
          
          print "RSSI collection sample collected. Trying to stop spawned process."
          kill(d.pid)
          
        try:
          Popen(["sudo","rm","-rf", "files/tmp/"+str(count)], stdout=DN, stderr=DN)
        except:
          print "File note deleted"
          
        
        count += 1
        
        stdout.flush()
        flush_input()
        
        # Remove all previous cap files (ie save storage space)
        try:
          if count%10==0:
            try:
              Popen(["sudo","rm","-rf", "files/tmp/"], stdout=DN, stderr=DN)
            except:
              print "File note deleted"
          
        except:
          print "Unable to really delete files"
    except:
      # alarm()
      stdout.flush()
      flush_input()
      stdout.flush()
      Popen(["sudo","rm","-rf", "files/tmp/"], stdout=DN, stderr=DN)
      print "\nError!!\n     "
      sys.exit()
      
    stdout.flush()

def rm(file):
  try:
    os.remove(file)
  except OSError:
    pass

if __name__ == '__main__':
  RC = RunConfiguration()
  RunEngine(RC).Start()

