#!/usr/bin/python

# -*- coding: utf-8 -*-
# Written to work for Python 2.7
import csv, os, time, random, errno, re, argparse, urllib, abc
import sys, stat, signal, psutil, termios, cPickle
from itertools import combinations as com
from subprocess import Popen, call, PIPE
from itertools import product as prod
from signal import SIGINT, SIGTERM
from sklearn.cluster import DBSCAN
from shutil import copy,rmtree
from sys import stdout, stderr
from tempfile import mkdtemp
from random import shuffle
import numpy as np
import pandas as pd


# Library Functions
#-=-=-=-=-=-=-=-=-=-

#https://stackoverflow.com/questions/45926230/how-to-calculate-1st-and-3rd-quartiles#answer-53551756
def find_median(sorted_list):
  indices = []

  list_size = len(sorted_list)
  median = 0

  if list_size % 2 == 0:
    indices.append(int(list_size / 2) - 1)  # -1 because index starts from 0
    indices.append(int(list_size / 2))

    median = (sorted_list[indices[0]] + sorted_list[indices[1]]) / 2
    pass
  else:
    indices.append(int(list_size / 2))

    median = sorted_list[indices[0]]
    pass

  return median, indices
  pass

def find_quarts(samples):  
  ''' Takes in a list and returns Q1, median, and Q2 for that list '''
  median, median_indices = find_median(samples)
  Q1, Q1_indices = find_median(samples[:median_indices[0]])
  Q2, Q2_indices = find_median(samples[median_indices[-1] + 1:])

  return [Q1, median, Q2]

# https://stackoverflow.com/questions/4789837/how-to-terminate-a-python-subprocess-launched-with-shell-true
def kill(proc_pid):
  process = psutil.Process(proc_pid)
  for proc in process.children(recursive=True):
    proc.kill()
  process.kill()
    
# https://stackoverflow.com/questions/2520893/how-to-flush-the-input-stream-in-python
def flush_input(): # only works on LINUX
  termios.tcflush(sys.stdin, termios.TCIOFLUSH)
  stdout.flush()

def alarm(message=""):
  '''Makes 12 beeps by writing "\a" 12 times on the same line'''
  print "\n."
  print (message)
  print ("\n")
  for i in range(0,12):
    time.sleep(0.3)
    print "\x1b[1A.",  
    print "\r           \n",

def rm(file):
  try:
    os.remove(file)
  except OSError:
    pass
    
def signal_handler(sig, frame):
  flush_input()
  print "Exited, successfully"
  sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
    
def findFile():
  wait = True
  
  while True:
    if not os.path.exists('files/scan-total.csv'):
      if wait:
        print "This script is supposed to be run after the first 30 inputs from the scan.py script have been generated\nPlease wait while the system finds the file.\nWaiting"
        wait = False
      else: print ".",
      time.sleep(0.5)
    else:
      if sum(1 for line in open('files/scan-total.csv')) >= 30: return
      else:
        if wait:
          print "This script is supposed to be run after the first 30 inputs from the scan.py script have been generated\nPlease wait while the system finds the file.\nWaiting"
          wait = False
        else: print "*",
        time.sleep(0.5)

#~=~=~=~=~=~=~=~=~=~

# Global Variables
#-=-=-=-=-=-=-=-=-=-
global normalProfile
normalProfile = dict()
learningPhaseDict = dict()
detectionPhaseDict = dict()

#~=~=~=~=~=~=~=~=~=~

# Common Functionality
#-=-=-=-=-=-=-=-=-=-
def loadNormalProfile():
  global normalProfile, learningPhaseDict, learningPhaseDict
  with open("files/normalProfile.cPickle", "rb") as backupFile:
    d = cPickle.load(backupFile)
    normalProfile, learningPhaseDict, learningPhaseDict = d[0],d[1],d[2]
    
def saveNormalProfile():
  dictionary = [normalProfile, learningPhaseDict, learningPhaseDict]
  with open("files/normalProfile.cPickle", "wb") as backupFile:
    cPickle.dump(dictionary, backupFile)


def InitializeIntraTimestamp(timestamp,Ph="learning"):  # Fast learning / detection
  ''' Generate Intra-timestamp Correlation  '''
  ''' Investigates patterns associated with samples from within a single time group   '''
  
  # Get the differences between each sample with a timestamp
  diff = [i[1] - i[0] for i in com(timestamp, 2)]
  # print timestamp
  # print diff
  
  normalProfile[Ph]["Intra"]["diff"] = diff
  # print "Timestamp: " + str(timestamp) + " | diff: " + str(diff)
  
  # initialize/store all timestamps 
  for i in range(len(timestamp)):
    if len(normalProfile[Ph]["Intra"]["hist"]) < len(timestamp):
      normalProfile[Ph]["Intra"]["hist"][i] = [timestamp[i]]
      normalProfile[Ph]["Intra"]["score"][i] = 0
    else:
      normalProfile[Ph]["Intra"]["hist"][i].append(timestamp[i])
  
  return
  
def InitializeInterTimestamp(timestamp, Ph="learning"):  # Fast learning / detection
  ''' Generate Inter-timestamp Correlation  '''
  ''' Investigates patterns associated with samples from one time group to the next   '''
  
  # Initialize Inter's Timestamp History list
  if len (normalProfile[Ph]["Inter"]["hist"]) ==0:
    # need two timestamps, so return on only one
    normalProfile[Ph]["Inter"]["hist"] = [timestamp]    
    return
  
  # Generate the differences between all dbm samples from one timestamp to the next
  diff = [a-b for a,b in prod(normalProfile[Ph]["Inter"]["hist"][-1], timestamp)]
  
  # hold the history of all differences in indecies
  for i in range(len(diff)):
    if len(normalProfile[Ph]["Inter"]["diff"]) < len(diff):
      normalProfile[Ph]["Inter"]["diff"][i] = [diff[i]]
      normalProfile[Ph]["Inter"]["score"][i] = 0
    else:
      normalProfile[Ph]["Inter"]["diff"][i].append(diff[i])
    
  # Store timestamp for next iteration (and other model uses)
  normalProfile[Ph]["Inter"]["hist"].append(timestamp)
  
  return

def DBmCorrelation(numberOfDBms, Ph="learning"):  # Slow learning / detection
  ''' Generate dBm Correlation  '''
  ''' Investigates patterns associated with samples' spread across lots of timestamps '''
  
  for i in range(numberOfDBms):
    normalProfile[Ph]["Corr"]["score"][i] = find_quarts(sorted(normalProfile[Ph]["Intra"]["hist"][i]))
  
    
  pass
  
def DBmClusterization(numberOfDBms, Ph="learning"): # Slow learning / detection
  ''' Generate dBm Correlation  '''
  ''' Investigates how samples cluster across lots of timestamps '''
  
  #this list to be returned back from this function
  overall_result = []
  
  #loop over each dbm datapoints(aka diff timestamps)
  for i in range(numberOfDBms):
    
    # EACH normalProfile[Ph]["Intra"]["hist"][i] has a list of samples at that given dBm level
    #get list of data for one dbm
    y = normalProfile[Ph]["Intra"]["hist"][i]
    # print y
    
    #make result list of clustering for this dbm
    result = []
    
    #keep only values between [-20 to -80] and put in a new list
    #note: use a library to make this block faster.
    x = []
    for j in y:
      if j>=20 and j<=80:
        x.append(j)
        
    # print (x)
    
    #do clustering
    clusters = DBSCAN_clustering_alg(x)
    
    #print clustering result
    # print("no of clusters: " + str(len(clusters)))
    
    # for k in range(0, len(clusters)):
      # print("cluster#" + str(k) + " len: " + str(len(clusters[k])))
      # print(clusters[k])
      
    #collect data only if clustering succeeded
    if(len(clusters)==1 and len(clusters[0])==0):
      #clustering failed, add empty lists in result list
      result.append([])
      result.append([])
      result.append([])
      overall_result.append(result)

    else:
      #clustering succeeded.
      #collect number of datapoints in each clusters in a list
      num_of_data_points = []
      for k in range(0, len(clusters)):
        num_of_data_points.append(len(clusters[k]));

      #collect average_num_of_points in all clusters
      average_num_of_points = []
      average_num_of_points.append((np.sum(num_of_data_points)) / len(clusters))
    
      #collect mean for each cluster
      cluster_mean_list = []
      for l in range(0, len(clusters)):
        one_cluster = clusters[l]
        mean = np.sum(one_cluster) / len(one_cluster)
        cluster_mean_list.append(mean)

      #add all collected data to the result list
      result.append(num_of_data_points)
      result.append(average_num_of_points)
      result.append(cluster_mean_list)

      #add the result list into the overall_result list
      overall_result.append(result)
    
  normalProfile[Ph]["Clust"]["score"] = overall_result
  return
  
  # return List that contain [# of points in each cluster (list of ints), (# of points in each cluster)/(# of clusters), mean for each cluster (list of floats/int)]
  
#mohammad's function for DBSCAN clustering with auto-adaptive parameters.
#Input: list of 1D integer datapoints as Python list.
#Output: list of lists containing clusters; lists can be empty.
def DBSCAN_clustering_alg(l):
    
  #sanity check for list.
  #if list is empty, no need for clustering.
  if(len(l)==0):
    return [[]]

  #compute parameters
  episode = np.ceil(np.std(l))
  min_samp_count = np.ceil(len(l)/episode)

  #sanity checks for parameters
  if (min_samp_count<0):
    min_samp_count=1
  if (episode<1):
    episode = 1
      
  #print clustering parameters
  #print("episode: " + str(episode) + "\n" + "min_samp_count: "+ str(min_samp_count))

  #convert python list into pandas dataframe.
  #lets name the column as "clientRSSI".
  #note: doesnt matter what we name it.
  X = pd.DataFrame(list(zip(l)), columns= ['clientRSSI'])

  #print pandas list
  #print(X)

  #clustering happening here
  db_default = DBSCAN(eps = episode, min_samples = min_samp_count).fit(X) 
  labels = db_default.labels_ 

  #with removing clustering noise
  #n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    
  #without removing clustering noise
  #note: noise results as a cluster.
  #and we need noise as a cluster,
  #since out datapoints are 
  #very close to each other.
  n_clusters_ = len(set(labels))

  #check if its only one cluster,
  #then we immediately return same list.
  if n_clusters_==1:
      
    #make list of list and return
    l1 = []
    l1.append(l)
    return l1
  else:
    #make list of lists to separate out the clusters
    clusters = []
    for i in range(0, n_clusters_):
      clusters.append([])

    #populate the list of lists
    for j in range(0, len(labels)):
      value = l[j]
      clusters[labels[j]-1].append(value)

    #return clusters
    return clusters

#~=~=~=~=~=~=~=~=~=~

# Main Functionality
#-=-=-=-=-=-=-=-=-=-

def learningPhase():  
  if not os.path.exists('files'): os.makedirs('files')
  
  findFile()
  
  print "\x1b[1A\r                                                  \a"
  print "File has been found. Please keep RSSI-common-scan.py running. This will take about 5 minutes to complete:\n\n"
  
  latestClock=0
  Phase = "learning"
  set="0"
  latestLine=0
  switch=False
  
  totalIterations = 4
  
  for system in ["Intra", "Inter", "Corr", "Clust"]:
      learningPhaseDict[system] = dict()
      learningPhaseDict[system]["score"] = dict()
  
  for iteration in range(totalIterations):
  
    for system in ["Intra", "Inter", "Corr", "Clust"]:
      normalProfile[Phase][system] = dict()
      for key in ["hist", "score", "diff"]:
        normalProfile[Phase][system][key] = dict()
        
    timestampsCollected=0
  
    while timestampsCollected < 40 : # Gather 120 timestamps
    
      with open('files/scan-total.csv') as csv_file:
        r = csv.reader(csv_file,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
        next(csv_file) #Skip headers
        timestamp=[]
        
        for sample in r:
          ''' sample[0] := Set, [1] := Clock, [2] := Antenna Strength, [3] := Client RSSI, [4] := IfAttackPresent ''' 
          # [4] only for actual validation of tool
          
          # If you have seen this value before, then don't look at it anymore
          if latestClock > float(sample[1]):
            # print sample[1]
            continue
          if timestampsCollected >= 40:
            continue
          
          latestLine += 1
          latestClock = float(sample[1])
          
          if sample[0] == set:
            timestamp += [abs(int(sample[3]))]
            switch = False
          elif switch == False: # First in set
            
          
            # Currently have a full timestamp
            InitializeIntraTimestamp(timestamp, Phase)
            InitializeInterTimestamp(timestamp, Phase)
            
            timestampsCollected += 1
            switch = True
            set = sample[0]
            timestamp = [abs(int(sample[3]))]
          # else:
            # alarm("[ERROR] scan-30.csv does not have consistent sets")
          
    # IntraTimestamp Functionality
      # How much should samples within the same timestamp change?
    # for i in range(len(normalProfile[Phase]["Intra"]["diff"])):
      # print normalProfile[Phase]["Intra"]["diff"]
    normalProfile[Phase]["Intra"]["score"] = find_quarts(sorted(normalProfile[Phase]["Intra"]["diff"]))
    
    # InterTimestamp Functionality
      # How much should samples change from timestamp to the next?
    for i in range(len(normalProfile[Phase]["Inter"]["diff"])):
      normalProfile[Phase]["Inter"]["score"][i] = find_quarts(sorted(normalProfile[Phase]["Inter"]["diff"][i]))
    
    DBmCorrelation(len(normalProfile[Phase]["Intra"]["hist"]), Phase)
    DBmClusterization(len(normalProfile[Phase]["Intra"]["hist"]), Phase)
    
    for system in ["Intra", "Inter", "Corr", "Clust"]:
      learningPhaseDict[system][iteration] = normalProfile[Phase][system]["score"]
      
    set = str(int(set) + 1)
    latestClock += 0.5
  
  print "-=-=-=-=-=-=-=-=-=-=-=-=-=-"
  
  # Initialize Final score elements for Learning Phase's Intra
  # -=-=-=-=-=-=-=-=-=-=-=-=-
        
  # [ [Q1,Median,Q3] * iterations ]  
  # [ [[Q1,Median,Q3] * # of perm] * iterations ]  <-- Inter
  # [ [[Q1,Median,Q3] * # of dBm ] * iterations ]   <-- Corr
  
  for system in ["Intra","Inter","Corr"]: 
    for perm in range(len(learningPhaseDict[system][0])):
      learningPhaseDict[system]["score"][perm] = dict()
      for a in ["Q1","Med","Q3"]:
        for b in [["_avg",0],["_max",0],["_min",999]]:
          if system == "Intra":
            learningPhaseDict[system]["score"][a+b[0]] = b[1]
          else:
            learningPhaseDict[system]["score"][perm][a+b[0]] = b[1]
      if system == "Intra":
        break
          
          
  # [ [[[ # in clust 1, ... * # of clust], [avg # of points], [mean for clust 1, ... * # of clust]] * # of dBms ] * iterations ]
  for perm in range(len(learningPhaseDict["Clust"][0])): # of dBms 
    learningPhaseDict["Clust"]["score"][perm] = dict() 
    for c in [0,1,2]: # 0 := # of pts per cluster, 1 := avg points (total), 2 := mean rssi per cluser
      learningPhaseDict["Clust"]["score"][perm][c] = dict() 
      for d in range(len(learningPhaseDict["Clust"][0][c])):
        # d := # of items in each list
        learningPhaseDict["Clust"]["score"][perm][c][d] = dict() 
        for a in ["Q1","Med","Q3"]:
          for b in [["_avg",0],["_max",0],["_min",999]]:
            learningPhaseDict["Clust"]["score"][perm][c][d][a+b[0]] = b[1]
  
      
  # Find min, max, and avearge for Q1,Med, and Q3 (Used for threshold values later)
  for i in range(totalIterations):
    iteration = learningPhaseDict["Intra"][i]
    for a in [["Q1",0],["Med",1],["Q3",2]]:
      if iteration[a[1]] > learningPhaseDict["Intra"]["score"][a[0]+"_max"]:
        learningPhaseDict["Intra"]["score"][a[0]+"_max"] = iteration[a[1]] 
      if iteration[a[1]] < learningPhaseDict["Intra"]["score"][a[0]+"_min"]:
        learningPhaseDict["Intra"]["score"][a[0]+"_min"] = iteration[a[1]] 
      if i+1 >= totalIterations:
        learningPhaseDict["Intra"]["score"][a[0]+"_avg"] =  ((learningPhaseDict["Intra"]["score"][a[0]+"_avg"] + iteration[a[1]] ) *1.0 / totalIterations * 1.0)
      else:
        learningPhaseDict["Intra"]["score"][a[0]+"_avg"] += iteration[a[1]]
      
  # +=-=-=-=-=-=+=-=-=-=-=-=+
  
  # Initialize Final score elements for Learning Phase's Inter and Corr
  # -=-=-=-=-=-=-=-=-=-=-=-=-

  # Find min, max, and avearge for Q1,Med, and Q3 (Used for threshold values later)
  for system in ["Inter","Corr"]: 
    for i in range(totalIterations):
      iteration = learningPhaseDict[system][i]
      for perm in range(len(iteration)):
        for a in [["Q1",0],["Med",1],["Q3",2]]:
          if iteration[perm][a[1]] > learningPhaseDict[system]["score"][perm][a[0]+"_max"]:
            learningPhaseDict[system]["score"][perm][a[0]+"_max"] = iteration[perm][a[1]] 
          if iteration[perm][a[1]] < learningPhaseDict[system]["score"][perm][a[0]+"_min"]:
            learningPhaseDict[system]["score"][perm][a[0]+"_min"] = iteration[perm][a[1]] 
          if i+1 >= totalIterations:
            learningPhaseDict[system]["score"][perm][a[0]+"_avg"] =  ((learningPhaseDict[system]["score"][perm][a[0]+"_avg"] + iteration[perm][a[1]] ) *1.0 / totalIterations * 1.0)
          else:
            learningPhaseDict[system]["score"][perm][a[0]+"_avg"] += iteration[perm][a[1]]
  
  # +=-=-=-=-=-=+=-=-=-=-=-=+ 

  # Find min, max, and avearge for Q1,Med, and Q3 (Used for threshold values later)
  for i in range(totalIterations):
    iteration = learningPhaseDict["Clust"][i]
    for perm in range(len(iteration)):
      for c in [0,1,2]:
        for d in range(len(iteration[perm][c])):
          for a in [["Q1",0],["Med",1],["Q3",2]]:
            # print learningPhaseDict["Clust"]["score"][perm][c][d][a[0]+"_max"]
            if iteration[perm][c][d] > learningPhaseDict["Clust"]["score"][perm][c][d][a[0]+"_max"]:
              learningPhaseDict["Clust"]["score"][perm][c][d][a[0]+"_max"] = iteration[perm][c][d]
            if iteration[perm][c][d] < learningPhaseDict["Clust"]["score"][perm][c][d][a[0]+"_min"]:
              learningPhaseDict["Clust"]["score"][perm][c][d][a[0]+"_min"] = iteration[perm][c][d]
            if i+1 >= totalIterations:
              learningPhaseDict["Clust"]["score"][perm][c][d][a[0]+"_avg"] =  ((learningPhaseDict["Clust"]["score"][perm][c][d][a[0]+"_avg"] + iteration[perm][c][d] ) *1.0 / totalIterations * 1.0)
            else:
              learningPhaseDict["Clust"]["score"][perm][c][d][a[0]+"_avg"] += iteration[perm][c][d]
  
  # print learningPhaseDict["Clust"] 
  # print " ** ** ** ** asdjfhaksdhlkfhaslkdfhlkshdlfhlasjfd"
      
  # print learningPhaseDict
  # Backup File for later use
  print "-=-=-=-=-=-=-\nLearning Profile has been created\n"
  saveNormalProfile()
  
  # len(timestamp)
  
  
def detectionPhase():  
  if not os.path.isfile("files/normalProfile.cPickle"): alarm("Normal Profile doesn't exist when Detection Phase")
  
  def initNormalProfile1(system):
    # [  [Q1,Median,Q3] * iterations]                 <-- Intra
    # [ [[Q1,Median,Q3] * # of perm ] * iterations ]  <-- Inter
    # [ [[Q1,Median,Q3] * # of dBm  ] * iterations ]  <-- Corr
    print system
    for perm in range(len(detectionPhaseDict[system][0])):
      detectionPhaseDict[system]["score"][perm] = dict()
      for a in ["Q1","Med","Q3"]:
        for b in [["_avg",0],["_max",0],["_min",999]]:
          if system == "Intra":
            print "INTRA"
            detectionPhaseDict[system]["score"][a+b[0]] = b[1]
          else:
            detectionPhaseDict[system]["score"][perm][a+b[0]] = b[1]
      if system == "Intra":
        break
  
  latestClock=0
  Phase = "detection"
  set="0"
  latestLine=0
  switch=False
  
  totalIterations = 4
  detectionPhaseDict = dict()
  contLearn = dict()
  
  for system in ["Intra", "Inter", "Corr", "Clust"]:
      detectionPhaseDict[system] = dict()
      detectionPhaseDict[system]["score"] = dict()
      contLearn[system] = dict()
      contLearn[system]["score"] = dict()
      contLearn[system]["score"]["pos"] = dict()
      contLearn[system]["score"]["neg"] = []
      for i in ["pos"]:
        if system == "Intra":
          for a in [0,1,2]:
            contLearn[system]["score"][i][a] = []
        if system in ["Inter","Corr"]:
          for b in range(len(learningPhaseDict[system]["score"])):
            contLearn[system]["score"][i][b] = dict()
            for a in [0,1,2]:
              contLearn[system]["score"][i][b][a] = []
        if system in ["Clust"]:
          for c in range(len(learningPhaseDict[system]["score"])):
            contLearn[system]["score"][i][c] = dict()
            for b in [0,1,2]:
              contLearn[system]["score"][i][c][b] = dict()
              for a in range(len(learningPhaseDict[system]["score"][c][b])):
                contLearn[system]["score"][i][c][b][a] = []
      
  contLearn["hist"]=[0,3] # [LastLine reached, attack present (unkown=3)]

  line_count = 0
  while True:

  
    for system in ["Intra", "Inter", "Corr", "Clust"]:
      normalProfile[Phase][system] = dict()
      for key in ["hist", "score", "diff"]:
        normalProfile[Phase][system][key] = dict()
        
    timestampsCollected=0
    contLearn["hist"][1] = 3
    
  
    while timestampsCollected < 40 : # Gather 120 Samples
    
      with open('files/scan-total.csv') as csv_file:
        r = csv.reader(csv_file,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
        next(csv_file) #Skip headers
        timestamp=[]
        
        for sample in r:
          ''' sample[0] := Set, [1] := Clock, [2] := Antenna Strength, [3] := Client RSSI, [4] := IfAttackPresent ''' 
          # [4] only for actual validation of tool
          
          # If you have seen this value before, then don't look at it anymore
          if latestClock > float(sample[1]):
            # print sample[1]
            continue
          if timestampsCollected >= 40:
            continue
          contLearn["hist"][0] += 1
          
          if len(sample)>3:
            if sample[4] == "1":
              contLearn["hist"][1] = 1
            elif not contLearn["hist"][1] == 1:
              if sample[4] == "0":
                contLearn["hist"][1] = 0
          
          line_count += 1
          latestLine += 1
          latestClock = float(sample[1])
          
          if sample[0] == set:
            timestamp += [abs(int(sample[3]))]
            switch = False
          elif switch == False: # First in set
            
          
            # Currently have a full timestamp
            InitializeIntraTimestamp(timestamp, Phase)
            InitializeInterTimestamp(timestamp, Phase)
            
            timestampsCollected += 1
            switch = True
            set = sample[0]
            timestamp = [abs(int(sample[3]))]
          # else:
            # alarm("[ERROR] scan-30.csv does not have consistent sets")
          
    # IntraTimestamp Functionality
      # How much should samples within the same timestamp change?
    # for i in range(len(normalProfile[Phase]["Intra"]["diff"])):
      # print normalProfile[Phase]["Intra"]["diff"]
    normalProfile[Phase]["Intra"]["score"] = find_quarts(sorted(normalProfile[Phase]["Intra"]["diff"]))
    
    # InterTimestamp Functionality
      # How much should samples change from timestamp to the next?
    for i in range(len(normalProfile[Phase]["Inter"]["diff"])):
      normalProfile[Phase]["Inter"]["score"][i] = find_quarts(sorted(normalProfile[Phase]["Inter"]["diff"][i]))
    
    DBmCorrelation(len(normalProfile[Phase]["Intra"]["hist"]), Phase)
    DBmClusterization(len(normalProfile[Phase]["Intra"]["hist"]), Phase)
    
    for system in ["Intra", "Inter", "Corr", "Clust"]:
      detectionPhaseDict[system] = normalProfile[Phase][system]["score"]
      
    set = str(int(set) + 1)
    latestClock += 0.5
  
    print "-=-=-=-=-=-=-=-=-=-=-=-=-=-"
    
    num_of_warns = 0.0
    
    
    contnTempt = dict()
    for system in ["Intra", "Inter", "Corr", "Clust"]:
      detc = detectionPhaseDict[system]
      lern = learningPhaseDict[system]["score"]     
      cont = contLearn[system]["score"]
      contnTempt[system] = []
      contn = contnTempt[system]
      
      if system == "Intra":
        # [Q1,Median,Q3]                 <-- Intra
        for a in [0,1,2]:
          
          if detc[a] >= lern['Q1_min'] -2 and detc[a] <= lern['Q3_max']+2:
            if detc[a]<= (lern['Med_avg']+ (lern['Q3_max'] - lern['Q1_min'])*1.0/2.0)+1 and detc[a] >= (lern['Med_avg'] - (lern['Q3_max'] - lern['Q1_min'])*1.0/2.0)-1 :
              # print "Completely Fine!"
              pass
            else:
              cont["pos"][a].append(detc[a])
              if len(cont["pos"][a]) > 4:
                q1,med,q3 = find_quarts(cont["pos"][a])
                if detc[a] >= q1 and detc[a] <= q3:
                  continue
              
              # Outside of "Normal" Data (But nothing to be alarmed about)
              print "[Warning] "+ system +": Potential to be anomaly"
              num_of_warns += 0.25
          else:
            contn.append(detc[a])
            if len(cont["neg"]) > 4:
              q1,med,q3 = find_quarts(cont["neg"])
              if detc[a] >= q1 and detc[a] <= q3:
                continue

            num_of_warns += 1
            print("[Warning] "+ system + ": out of bounds has been triggered." + str(detc[a]) + " is outside range of [" + str(lern['Q1_min'] -2) +","+ str(lern['Q3_max']+2) + "]")
            
      if system in ["Inter","Corr"]:
        # [[Q1,Median,Q3] * # of perm ]  <-- Inter
        # [[Q1,Median,Q3] * # of dBm  ]  <-- Corr
        for b in range(len(lern)):
          
          for a in [0,1,2]:
            if detc[b][a] >= lern[b]["Q1_min"]-2 and detc[b][a]  <= lern[b]["Q3_max"]+2:
              if detc[b][a]  <= (lern[b]["Med_avg"] + (lern[b]["Q3_max"] - lern[b]["Q1_min"])*1.0/2.0)+1 and detc[b][a]  >= (lern[b]["Med_avg"] - (lern[b]["Q3_max"] - lern[b]["Q1_min"])*1.0/2.0)-1:
                # print "Completely Fine!"
                pass
              else:
                cont["pos"][b][a].append(detc[b][a])
                if len(cont["pos"][b][a]) > 5:
                  q1,med,q3 = find_quarts(cont["pos"][b][a])
                  if detc[b][a] >= q1 and detc[b][a] <= q3:
                    continue
                # Outside of "Normal" Data (But nothing to be alarmed about)
                print "[Warning] "+ system +": Potential to be anomaly"
                num_of_warns += 0.25
            else:
              contn.append(detc[b][a])
              if len(cont["neg"]) > 4:
                q1,med,q3 = find_quarts(cont["neg"])
                if detc[a] >= q1 and detc[a] <= q3:
                  continue
              num_of_warns += 1
              print("[Warning] "+ system + ": out of bounds has been triggered." + str(detc[b][a]) + " is outside range of [" + str(lern[b]['Q1_min'] -2) +","+ str(lern[b]['Q3_max']+2) + "]")
              # print "alarm"
      
      if system == "Clust":
        #  [[[ # in clust 1, ... * # of clust], [avg # of points], [mean for clust 1, ... * # of clust]] * # of dBms ]    <-- Cluster
        
        for c in range(len(lern)): # c'th dBm level
          for b in [0,1,2]: # # 0 := # of pts per cluster, 1 := avg points (total), 2 := mean rssi per cluser
            tempLearned = len(lern[c][b])
            for p in range(len(lern[c])):
              if (lern[c][b][p]['Q3_min']==999):
                tempLearned -= 1
            
            if tempLearned == len(detc[c][b]) :

                for a in range(len(detc[c][b])):
                  # a := # of clusters

                  if detc[c][b][a] >= lern[c][b][a]['Q1_min']-2 and detc[c][b][a] <= lern[c][b][a]['Q3_max']+2:
                    if detc[c][b][a] <= lern[c][b][a]['Med_avg'] + ((lern[c][b][a]['Q3_max']-lern[c][b][a]['Q1_min'])*1.0/2.0)+1 and detc[c][b][a] >= lern[c][b][a]['Med_avg'] - ((lern[c][b][a]['Q3_max']-lern[c][b][a]['Q1_min'])*1.0/2.0)-1:
                    # Is it within "Normal" Range?
                    
                      pass
                    else:
                      # Outside of "Normal" Data (But nothing to be alarmed about)
                      print "[Warning] "+ system +": Potential to be anomaly"
                      num_of_warns += 0.01
                  else:
                    cont["pos"][c][b][a].append(detc[c][b][a])
                    if len(cont["pos"][c][b][a]) > 4:
                      q1,med,q3 = find_quarts(cont["pos"][c][b][a])
                      if detc[c][b][a] >= q1 and detc[c][b][a] <= q3:
                        continue
                    num_of_warns += 0.15
                    print("[Warning] "+ system + ": out of bounds has been triggered." + str(detc[c][b][a] ) + " is outside range of [" + str(lern[c][b][a]['Q1_min']-2) +","+ str(lern[c][b][a]['Q3_max']+2) + "]")
            else:
              print ("[Warning] " + system + " : number of clusters." + str(tempLearned) + " does not equal " + str(len(detc[c][b]))) 
              num_of_warns += 0.3
    
    did_alarm = 3
    if num_of_warns >= 15:
      print "ALARM at: " + str(line_count) + " actually: " + str(contLearn["hist"][1]) + " at score: " + str(num_of_warns)
      # alarm("[Alarm] Potential Attack Happening!!")
      did_alarm = 1
    else:
      print "No alarm at: " + str(line_count) + " actually: " + str(contLearn["hist"][1]) + " at score: " + str(num_of_warns)
      # alarm("[CLEAR] No attack happening!!")
      for system in ["Intra", "Inter", "Corr", "Clust"]:
        for i in contnTempt[system]:
          contLearn[system]["score"]["neg"].append(i)
      did_alarm = 0
      
    with open("files/output", "a+") as csvf:
      w = csv.writer(csvf,delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
      w.writerow([str(line_count),did_alarm, str(contLearn["hist"][1]), str(num_of_warns)])
          
    # print detectionPhaseDict

  
#~=~=~=~=~=~=~=~=~=~

if __name__ == '__main__':

  # All of the parser stuff
  parser = argparse.ArgumentParser(description='ALT-RSSI: Alternating Strength to Detect MAC Spoof\n[Learning Script]\n\nThis is the program meant for specifically learning a new enviornment',formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('-nl','-nL','--noLearning', action='store_true', help='Skip Learning and load normal profile [requires presence of files/normalProfile.cPickle]')
  parser.add_argument('-nd','-nD','--noDection', action='store_true', help='Skip Detection Phase. Typically, this is only to generate a normal profile with Learning Phase')
  
  global args, DN
  args = parser.parse_args()
  DN = open(os.devnull, 'w')
  
  # global variables for models
  for i in ["learning","detection"]:
    normalProfile[i] = dict()
    for system in ["Intra", "Inter", "Corr", "Clust"]:
      normalProfile[i][system] = dict()
      for key in ["hist", "score", "diff"]:
        normalProfile[i][system][key] = dict()
  
  if args.noLearning:
    loadNormalProfile()
  else:
    learningPhase()
    
  if not args.noDection:
    detectionPhase()
  
