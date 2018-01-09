#!/usr/bin/env python
# -*- coding: utf-8 -*-

from splpioneer.VariabilityModel import *
from splpioneer.Project import *
from splpioneer.Build import *
from splpioneer.Benchmarker import *
from splpioneer.MultiBenchmarker import *
from splpioneer import copy, PROJECT_BUILD_PATH

from multiprocessing import Pool as ThreadPool 

global ThreadPool
"""
xz = Project('xz')
print len(xz.getCommits())

bener = MultiBenchmarker('xz', 'resources/xz_updated.xml', ('canterbury_corpus.tar', ''))
bener.preprocess(2, 2) #T-2 sampling w/ 2 numeric samples => 24 variants
bener.run_benchmark(10, 6) # 10 repetitions, 6 threads  
"""

X264 = Project("xz")

vm = VariabilityModel("resources/xz_updated.xml")
vm.parse_vm()

grammar = vm.build_grammar()

#print len(grammar.get_all_configurations())
#sample = grammar.sampleTWise(2, 4)
#print(len(sample)) # 8

build = Build(X264, "0b0e1e6803456aac641a59332200f8e95e2b7ea8")
benchmarker = Benchmarker(build, sample, vm, n = 5)
benchmarker.run('sintel_trailer_2k_480p24.y4m', '-o output.ogg')
"""
def benchmark(hexsha):
    build = Build(X264, hexsha)
    benchmarker = Benchmarker(build, sample, vm, n = 5)
    benchmarker.run('sintel_trailer_2k_480p24.y4m', '-o output.ogg')


commitz = X264.getCommits() #["94e3f986aa4e14b4ff01ac24857f499630d6d180"]#,"0b0e1e6803456aac641a59332200f8e95e2b7ea8","a015cd1f90116e655be4eaf4aad42c4c911c2807", "c2e29f06a7d1e3ba242ac2fafc69f5d6e92f62cd"]
##print commitz
pool = ThreadPool(2) 
pool.map(benchmark, commitz)
"""