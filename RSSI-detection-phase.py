#!/usr/bin/python

# -*- coding: utf-8 -*-
# I used: https://mubaris.com/posts/kmeans-clustering/ for help with K-Means
from copy import deepcopy
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.cluster import KMeans
from statistics import mean 
import warnings
warnings.simplefilter("ignore")

# Written to work for Python 2.7
import csv, os, time, random, errno, re, argparse, urllib, abc
from sys import argv, stdout
from shutil import copy
from subprocess import Popen, call, PIPE
from signal import SIGINT, SIGTERM
from tempfile import mkdtemp
from random import shuffle
import signal
import sys
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
  '''Makes 12 beeps by writing "\a" 12 times on the same line'''
  print "\n\a."
  for i in range(0,12):
    time.sleep(0.3)
    print "\x1b[1A.\a",  #Go up one line
    print "\r           \n",
    
def detectionPhase():

  if not os.path.exists('files/newLearned.csv'): 
    with open('files/newLearned.csv','w') as csv_file:
      w = csv.writer(csv_file,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
      w.writerow(["0dBavg","5dBavg","10dbavg","15dBavg","20dBavg","25dBavg","30dBavg","ClusterScore1avg","ClusterScore2avg","NumOfEntries"])
      
  if not os.path.exists('files/negative.csv'): 
    with open('files/negative.csv','w') as csv_file:
      w = csv.writer(csv_file,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
      w.writerow(["0dB","5dB","10db","15dB","20dB","25dB","30dB","ClusterScore1","ClusterScore2"])
  
  if not os.path.exists('files/detections.csv'): 
    with open('files/detections.csv','w') as csv_file:
      w = csv.writer(csv_file,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
      w.writerow(["0dBavg","5dBavg","10dbavg","15dBavg","20dBavg","25dBavg","30dBavg","ClusterScore1avg","ClusterScore2avg","NumOfEntries"])
  
  print "This script is supposed to be run after RSSI-learning-phase.py.\n"
  
  print "Please wait while the system finds files/scan-30.csv.\nWaiting",
  while True:
    if not os.path.exists('files/scan-30.csv'):
      print ".",
      time.sleep(0.5)
    else:
      if sum(1 for line in open('files/scan-30.csv')) >= 30:
        break
      else:
        print "*",
        time.sleep(0.5)
  print "\x1b[1A\x1b[1A\r                                                  \a"
  print "File has been found. System will now try to detect files/learned.csv\nWaiting"
  while True:
    if not os.path.exists('files/learned.csv'):
      print ".",
      time.sleep(0.5)
    else:
      break
  print "\x1b[1A                                                                     \x1b[1A                                                                               \x1b[1A\r                                                                               \x1b[1A\a"
  
  
  ld=[]
  with open('files/learned.csv','r') as csv_file:
    r = csv.reader(csv_file,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
    next(csv_file)
    for l in r:
      for i in l:
        ld.append(mean((map(float, i.strip('[ ]').split(',')))))
        
  # Take info from learning phase => threshold values
  db0,db5,db10,db15,db20,db25,db30,ClusterScore1,ClusterScore2,gainThreshold,score1Threshold,score2Threshold = ld[0],ld[1],ld[2],ld[3],ld[4],ld[5],ld[6],ld[7],ld[8],ld[9],ld[10],ld[11]
     
  
  clientStats=[[],[],[],[],[],[],[],[],[],[],[]]
  #First 7 are attenna gain strength, last four are scores for 1 cluster and 2 clusters
  
  maxRSSI,minRSSI,maxScore1,minScore1,maxScore2,minScore2=0,9999999999999,0,9999999999999,0,9999999999999
  
  while True:
    try:
      time.sleep(1.1)
      clientArray=[[],[],[],[],[],[],[],[],[]]
      clientRSSI=[]
      antennaSTR=[]
      with open('files/scan-30.csv') as csv_file:
        r = csv.reader(csv_file,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
        next(csv_file)
        for l in r:
          current=-1
          currentDBI=0
          for i in l:
            current += 1
            if current == 0:
              currentDBI=int(i)-1
              antennaSTR.append(currentDBI)
            if current == 1:
              if not(i==0):
                rs = abs(int(i))
                clientArray[currentDBI].append(rs)
                if rs > maxRSSI:
                  maxRSSI = rs
                if rs < minRSSI:
                  minRSSI = rs
              clientRSSI.append(rs)
              break
      
      print clientArray
      for l in range(0,7):
        clientStats[l].append(mean(clientArray[l]))
              
      # Importing the dataset
      # data = pd.read_csv('files/scan-30.csv')

      # Getting the values and plotting it
      X = np.array(list(zip(clientRSSI, antennaSTR)))
      
      for k in [1,2]: # Number of clusters
      
          kmeans = KMeans(n_clusters=k)
          # Fitting the input data
          kmeans = kmeans.fit(X)
          # Getting the cluster labels
          labels = kmeans.predict(X)
          
          score = kmeans.score(X)
          
          clientArray[k+6].append(score)
          # clientArray[2*k+6].append(str(kmeans.cluster_centers_))
          
          if k == 1:
            if score > maxScore1:
              maxScore1 = score
            if score < minScore1:
              minScore1 = score
          else:
            if score > maxScore2:
              maxScore2 = score
            if score < minScore2:
              minScore2 = score
      
      # Unsupervised Learning
      prev=[[],[],[],[],[],[],[],[],[],[]]
      needMoreData = True
      with open('files/newLearned.csv','r') as csv_file:
        r = csv.reader(csv_file,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
        next(csv_file)
        
        for l in r: #Because indices don't work apperently
          count=0
          for i in l:
            
            a = mean(map(float, i.strip('[ ]').split(',')))
            if a != 0.0:
              prev[count].append(a)
              needMoreData=False
            count += 1
      
      
      
      if not(needMoreData):
        for p in range(0,len(prev)):
          # print "Prev: " + str(prev) + "P: " + str(p)
          try:
            prev[p]=mean(prev[p])
          except:
            needMoreData=True
            break
          
        
      passed=True
      # try:
      if len(prev)>7 and not(needMoreData):
        for i in range (0,9):
          # print "Check: " + str(mean(clientArray[i])) + " : " + str(prev[i]) +"|"+str(score1Threshold) +"\n"
          if i<7 and (abs(mean(clientArray[i]) - prev[i]) > gainThreshold/2):
            print "ClientRSSI on i: "+str(i)+" at: " + str(mean(clientArray[i])) + " is outside the range of " + str(prev[i]) + " +- " + str(gainThreshold/2)
            passed=False
          elif i==7 and (abs(mean(clientArray[i]) - prev[i]) > score1Threshold/2):
            print "ClientRSSI on i: "+str(i)+" at: " + str(mean(clientArray[i])) + " is outside the range of " + str(prev[i]) + " +- " + str(score1Threshold/2)
            passed=False
          elif i==8 and (abs(mean(clientArray[i]) - prev[i]) > score2Threshold/2):
            print "ClientRSSI on i: "+str(i)+" at: " + str(mean(clientArray[i])) + " is outside the range of " + str(prev[i]) + " +- " + str(score2Threshold/2)
            passed=False
      else:
        print "Waiting for more data"
      # except:
        # print "Waiting for more data."
        # prev=[]
        # passed=True
      
      # If it is a good reading, add it to the training set
      if passed:
        print "No attack found. Score: " + str(clientArray[7]) + ":" +str(clientArray[8])+ ".\n"
        with open('files/newLearned.csv','a+') as csv_file:
          w = csv.writer(csv_file,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
          tw=[0,0,0,0,0,0,0,0,0,0,0]
          if len(prev)>8 and not(needMoreData):
            # for i in range(0,9): print "ClientArray:" + str(clientArray[i]) + " | " + str(mean(clientArray[i])) + "| prev: "+ str(prev[i]) + "\n"
            w.writerow([(mean(clientArray[0])+prev[0]*prev[9])/(prev[9]+1),(mean(clientArray[1])+prev[1]*prev[9])/(prev[9]+1),(mean(clientArray[2])+prev[2]*prev[9])/(prev[9]+1),(mean(clientArray[3])+prev[3]*prev[9])/(prev[9]+1),(mean(clientArray[4])+prev[4]*prev[9])/(prev[9]+1),(mean(clientArray[5])+prev[5]*prev[9])/(prev[9]+1),(mean(clientArray[6])+prev[6]*prev[9])/(prev[9]+1),(mean(clientArray[7])+prev[7]*prev[9])/(prev[9]+1),(mean(clientArray[8])+prev[8]*prev[9])/(prev[9]+1),(prev[9]+1) ])
          else:
            
            # for i in range(0,9): 
              # print "ClientArray:" + str(clientArray[i]) + " | " + str(mean(clientArray[i])) +"\n"
            w.writerow([mean(clientArray[0]),mean(clientArray[1]),mean(clientArray[2]),mean(clientArray[3]),mean(clientArray[4]),mean(clientArray[5]),mean(clientArray[6]),mean(clientArray[7]),mean(clientArray[8]),(1) ])
          
        with open('files/negative.csv','a+') as csv_file:
          w = csv.writer(csv_file,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
          w.writerow([clientArray[0],clientArray[1],clientArray[2],clientArray[3],clientArray[4],clientArray[5],clientArray[6],clientArray[7],clientArray[8]])
          
      # If it is not a good reading, then throw an alarm!   
      else:
        print "OH NO!! We have detected a MAC Spoofing attack!\n"
        prevBad=[[],[],[],[],[],[],[],[],[]]
        with open('files/detections.csv','r') as csv_file:
          r = csv.reader(csv_file,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
          next(csv_file)
          
          for l in r: #Because indices don't work apperently
            for i in l:
              prevBad.append(mean(map(float, i.strip('[ ]').split(','))))
        
        with open('files/detections.csv','a+') as csv_file:
          w = csv.writer(csv_file,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
          tw=[]
          
          try:
            for i in range(0,9): tw.append((mean(clientArray[i])+prevBad[i]*prevBad[9])/(prevBad[9]+1))
            
            w.writerow([tw[0],tw[1],tw[2],tw[3],tw[4],tw[5],tw[6],tw[7],tw[8],(prevBad[9]+1) ])
          except:
            for i in range(0,9): tw.append((mean(clientArray[i])))
            w.writerow([tw[0],tw[1],tw[2],tw[3],tw[4],tw[5],tw[6],tw[7],tw[8],(1) ])
          
        alarm()
        print "Bad input added to Positive detection list"
    except KeyboardInterrupt:
    
      print "\nCTRL+C Hit!!\n     "
      sys.exit()


if __name__ == '__main__':
  detectionPhase()

