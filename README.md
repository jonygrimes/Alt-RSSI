# Alt-RSSI
Texas A&amp;M University

# Idea

Wireless communication, especially  WiFi communication is prone to many attacks. Due to the nature of WiFi protocol, its easier for an attacker to hijack a victim's MAC and sink all traffics to the attacker machine. To detect MAC spoofing attack, our solution provides a novel way that samples client's signals strength at the access point, and uses statistical analysis and machine learning approach to detect an attack. Our proposed solution can detect a MAC spoofing attack with a 95 \% Precision.

# Data
Included in this repository is a series of data collected from previous experiments found in the "data" folder; details can be found in the associated paper.

To simulate any of these attacks, simply copy one of these .csv files into the "files" folder and rename it to "scan-total.csv". From there simply run:
`python RSSI-tool.py`

The results will apear on the screen.

# How to run Alt-RSSI
Alt-RSSI is broken up into two pieces: RSSI-scan.py and RSSI-tool.py.

## RSSI-scan.py
This program collects RSSI signals at different attenna gain strengths that you specify.

To properly test this, you should ensure that your computer has a wireless interface that can be put into promiscous mode and that your computer has hostapd:
`sudo apt install hostapd`

To begin, you will need to set your antenna into promiscuous by running the following:
`airmon-ng start [your wireless interface]`

Then, you can start RSSI-scan.py by using the following:
`python RSSI-scan.py -m [client MAC address] -d [list of dBm you wish to run at] -i [raw (un-promiscuous) interface] -p [promiscuous interface]`

You can either run this tool as you are using RSSI-tool.py or use it to collect samples to be tested later.

## RSSI-tool.py
This program evaluates the collected samples for any deviations in the expected normal behavior (found in the first 80 timestamps of data).

To begin, please ensure that you have a file called "scan-total.csv" in a directory called "files" and that "files" is in the same directory as RSSI-tool.py.

To run this tool, simply run:
`python RSSI-tool.py`

This will run through the file called "files\scan-total.csv", train on the first 80 timestamps, and then test the remaining lines in this file. Once completed, RSSI-tool.py will continue to wait for new lines to appear in "files\scan-total.csv" from RSSI-scan.py. So, to stop the processing, simply type "CTRL+C".

### Additional Features
To use an existing Normal Profile, ensure that the "files\normalProfile.cPickle" file is present from a previous iteration, run:
`python RSSI-tool.py -nL`

To only create a Normal Profile, run:
`python RSSI-tool.py -nD`

### Meaning of output
After each 40 timestamps, a message will appear:
`No alarm at: (last line number in timestamp) actually: (attack) at score: (Alt-RSSI score)`
or
`ALARM at: (last line number in timestamp) actually: (attack) at score: (Alt-RSSI score)`

This indicates whether an alarm actually went off or not. Additionall, the "attack" is something that is indicated in the provided data, which was manually tagged if there was actually an attack happening or not; in real data, this would be unknown and therefore set to "3". The "Alt-RSSI" score is a number given to indicate how confident we are in that score; a 15 is where the decision boundary is.

`[Warning] Inter: (message)`
This indicates that there was a distubance, but just because a warning shows up, doesn't mean that there is anything to be worried about.
