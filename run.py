#!/usr/bin/env python
# -*- coding: utf-8 -*-

import commands

from splpioneer.VariabilityModel import *
from splpioneer.Project import *
from splpioneer.Build import *
from splpioneer.Benchmarker import *

from statistics import stdev, mean, median

import numpy as np

def normCV(xs):
    return (np.percentile(xs, 75) - np.percentile(xs, 25))/np.percentile(xs, 50)
    
video = " -o bener.ogg bridge_far_qcif.y4m" # small

# 2 systems, 3 variants (slow, medium, fast), 2 benchmarks (small, medium, big)
systems =   {"xz":["xz -9 --keep --force canterbury_corpus.tar", 
                   "xz -6 --keep --force canterbury_corpus.tar", 
                   "xz -2 --keep --force canterbury_corpus.tar",
                   "xz -9 --keep --force cantrbry3.tar",
                   "xz -6 --keep --force cantrbry3.tar",
                   "xz -2 --keep --force cantrbry3.tar"], 
             "264": ["x264 --quiet --b-adapt  2   --direct   auto   --me   umh   --partitions   all --rc-lookahead 60 --ref 8 --subme 9 --trellis 2" + video, 
                     "x264 " + video,
                     "x264 --no-mixed-refs --rc-lookahead 20 --ref 2 --subme 4 --weightp 1" + video]}

# TODO select arbitrary variants and versions 

repetitions = [3,4,5,6,7,8,9,10,15,20,25,50]

with open('results.csv', 'a') as file:
    newFileWriter = csv.writer(file)
    
    for system in systems.keys():
        for operation in systems[system]:
            
            command = "/usr/bin/time -f '%U' " + operation
            #print command
            for repetition in repetitions:
                
                outputs = []
                for r in range(repetition):
                    output = commands.getstatusoutput(command)[1].split("\n")[-1]
                    #print output
                    outputs.append( float( output) )
                 
                e = np.percentile(outputs, 50)
                abweichung = normCV(outputs) #normiert
                
                # append measurement to records
                newFileWriter.writerow([command, repetition, e, abweichung])
                
                print repetition, e, abweichung
            
            