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
    
def learningPhase():
  if not os.path.exists('files'): os.makedirs('files')
  
  print "This script is supposed to be run after the first 30 inputs from the scan.py script have been generated\n"
  
  print "Please wait while the system finds the file.\nWaiting",
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
  print "\x1b[1A\r                                                  \a"
  print "File has been found. Please keep scan.py running. This will take about 5 minutes to complete:\n\n"
  
  clientStats=[[],[],[],[],[],[],[],[],[],[],[],[]]
  #First 7 are attenna gain strength, next 2 are scores for 1 cluster and 2 clusters, last 3 are for ranges for threshold
  maxRSSI,minRSSI,maxScore1,minScore1,maxScore2,minScore2=0,9999999999999,0,9999999999999,0,9999999999999
  
  for iteration in range(0, 200):
    
    time.sleep(1)
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
    
            
    for l in range(0,7):
      clientStats[l].append(mean(clientArray[l]))
            
    # Importing the dataset
    # data = pd.read_csv('files/scan-30.csv')

    # Getting the values and plotting it
    X = np.array(list(zip(clientRSSI, antennaSTR)))
    # print "ARRAY: " + str(X) + "\n\n"
    
    for k in [1,2]: # Number of clusters
    
        kmeans = KMeans(n_clusters=k)
        # Fitting the input data
        kmeans = kmeans.fit(X)
        # Getting the cluster labels
        labels = kmeans.predict(X)
        score = kmeans.score(X)
        
        clientStats[k+6].append(score)
        # clientStats[2*k+6].append(str(kmeans.cluster_centers_))
        
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
            
    clientStats[9].append(maxRSSI-minRSSI)
    clientStats[10].append(maxScore1-minScore1)
    clientStats[11].append(maxScore2-minScore2)
    
    if (iteration % 10 == 0):
      print "\x1b[1A\r\033[1;96mProgress\033[0m: [" + '\033[32m=' * (iteration/10) + '\033[31m-' * (20-iteration/10) + "\033[0m] " + str(iteration) + "/200"
      
    elif (iteration % 5 == 0):
      print "\x1b[1A\r\033[1;96mProgress\033[0m: [" + '\033[32m=' * (int(iteration/10)) + '\033[38;5;215m~' + '\033[31m-' * (int(20-iteration/10)-1) + "\033[0m] " + str(iteration) + "/200"
  print "\x1b[1A\r\033[1;96mProgress\033[0m: [" + ('\033[32m=' * (int(20))) + "\033[0m] 200/200"
                   
  with open('files/learned.csv','w') as csvfile:
    w = csv.writer(csvfile,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
    w.writerow(["0dB","5dB","10db","15dB","20dB","25dB","30dB","ClusterScore1","ClusterScore2","rssiThreshold","score1Threshold","score2Threshold"])
    w.writerow([mean(clientStats[0]),mean(clientStats[1]),mean(clientStats[2]),mean(clientStats[3]),mean(clientStats[4]),mean(clientStats[5]),mean(clientStats[6]),mean(clientStats[7]),mean(clientStats[8]),mean(clientStats[9]),mean(clientStats[10]),mean(clientStats[11])])
    
  print "Intial learning has completed, please begin to run the detection system\a."


if __name__ == '__main__':
  learningPhase()

