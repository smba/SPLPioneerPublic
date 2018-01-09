'''
Created on Oct 30, 2017

@author: stefan
'''
from multiprocessing.pool import ThreadPool

from splpioneer.Benchmarker import Benchmarker
from splpioneer.Build import Build
from splpioneer.Project import Project
from splpioneer.VariabilityModel import VariabilityModel


class MultiBenchmarker:
    def __init__(self, project, variability_model, benchmark_tupel):
        self.project = Project( project )
        self.vm = VariabilityModel( variability_model )
        self.benchmark_tupel = benchmark_tupel
        
        self.vm.parse_vm()
        self.grammar = self.vm.build_grammar()
    
    def preprocess(self, t, n):
        self.sample = self.grammar.sampleTWise(t, n)
        print len(self.sample)
    
    def run_benchmark(self, repetitions, poolsize):
        
        def benchmark(hexsha):
            build = Build(self.project, hexsha)
            #build.build()
            benchmarker = Benchmarker(build, self.sample, self.vm, n=repetitions)
            benchmarker.run(self.benchmark_tupel[0], self.benchmark_tupel[1])
            
        pool = ThreadPool( poolsize ) 
        results = pool.map(benchmark, self.project.getCommits())
