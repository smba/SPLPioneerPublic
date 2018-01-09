#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import errno
from statistics import mean, median
import numpy as np

RESOURCES = os.getcwd() + "/resources"

""" Path to the Git repository of a project """
PROJECT_PATH = lambda name: RESOURCES + "/" + name + "/repository"

""" Path to the build directory of project """
#PROJECT_BUILD_PATH = lambda name: RESOURCES + "/" + name + "/build"

def PROJECT_BUILD_PATH(name, hexsha):
    return RESOURCES + "/" + name + "/build/" + hexsha

kpis = ['time_e', 'time_S', 'time_U', 'memory_M', 'memory_t', 'memory_K', 'memory_D', 'memory_p', 'memory_X', 'memory_Z', 'throughput_I', 'throughput_O', 'throughput_r', 'throughput_s', 'throughput_k' ]

def mad(arr):
    arr = np.ma.array(arr).compressed() # should be faster to not use masked arrays.
    med = np.median(arr)
    return np.median(np.abs(arr - med))

def copy(src, dst):
    try:
        os.system("rm -rf " + dst)
        shutil.copytree(src, dst)
    except OSError as exc: 
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else: raise
        
def frange(minimum, maximum, step):
    x = minimum
    while x <= maximum:
        yield x
        x += step

def xml_list(node):
    if node == None:
        return[]
    if isinstance(node, list): # is list
        return node
    return [node] # is no list, so create one

def geo_mean_overflow(iterable):
    a = np.log(iterable)
    return np.exp(a.sum()/len(a))

def matrix_aggregate(data, n, method = 'median'):
    transposed = [ [] for i in range(n)]
    for vector in data:
        for i in range(n):
            transposed[i].append(vector[i])
    if method == 'median':
        return list(map(lambda l: median(l), transposed))
    elif method == 'arithmetic mean':
        return list(map(lambda l: mean(l), transposed))
    elif method == 'geometric mean':
        return list(map(lambda l: geo_mean_overflow(l), transposed))
    elif method == 'iqr':
        return list(map(lambda l: iqr(l), transposed))
    elif method == 'mad':
        return list(map(lambda l: mad(l), transposed))
    
def iqr(data):
    return np.subtract(*np.percentile(data, [75, 25]))

def parse_number(s):
    if s.isdigit():
        return int(s)
    elif s.count('.') == 1 and ''.join(s.split('.')).isdigit():
        return float(s)
    
