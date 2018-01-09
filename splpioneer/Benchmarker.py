#!/usr/bin/env python
# -*- coding: utf-8 -*-

from string import Template
import os
import time
import commands
import csv
from splpioneer import parse_number, matrix_aggregate, iqr, kpis
import sqlite3 as sql

from ProcessTime import ProcessTime

import math

class Benchmarker:
    
    
    """
    Initializes a benchmarker instance that can run variants and measure non-functional 
    parameters. Possible parameters can be specified by adding formstrings to the nf_parameters list:
    
    K    Average total (data+stack+text) memory use of the process, in Kbytes.
    e    Elapsed real time (in seconds)
    I    Number of filesystem inputs by the process.
    O    Number of filesystem outputs by the process.
    
    ... find more in the man page for /usr/bin/time (GNU version of 'time')
    
    build splpioneer.diachrony.Build instance to run and configure
    vm splpioneer.variability.VariabilityModel instance to derive configurations from
    nf_parameters
    """
    
    
    def __init__(self, build, configurations, vm, n = 3, nf_parameters=['e','S','U','M','t','K','D','p','X','Z','I','O','r','s','k','x'], aggregation_method = 'median'):
          
        self.build = build
        self.vm = vm
        #self.progress = progress
        self.nf_parameters = nf_parameters
        self.n = n
        self.export_path = "../" + self.build.project.name + "_" + self.build.hexsha + ".csv"
        self.aggregation_method = aggregation_method
        self.configurations = configurations
        # Check if GNU version of time is installed
        assert os.path.isfile("/usr/bin/time"), "GNU version of time could not be found!"

    
    """
    Executes the benchmark for a single version and all given configurations
    
    16.10. removing database use, use csv file export instead 
    """
    def run(self, benchmark_file, benchmark_postfix ):
        timestamp = int(math.floor(time.time()))
        binary_options = sorted(list(map(lambda x: x.name, filter(lambda x: x.typ == "binary", self.vm.configuration_options.values()))))
        numeric_options = sorted(list(map(lambda x: x.name, filter(lambda x: x.typ == "numeric", self.vm.configuration_options.values()))))
        if 'root' in binary_options: binary_options.remove('root')

        # add record file header
        record_name = self.build.project.name + '/' + self.build.project.name + "_" + self.build.hexsha + ".csv"
        os.system('rm -rf ' + record_name)
        
        if not os.path.exists(str(self.build.project.name)):
            os.system('mkdir ' + str(self.build.project.name))
            
        mad_labels = list(map(lambda x: x + '_mad', self.nf_parameters))
            
        with open(record_name, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(binary_options + numeric_options + self.nf_parameters + mad_labels)
         
        N = self.n
        configurations = self.configurations#self.vm.get_all_configurations()
        
        tasks = len(configurations) * N

        keys = self.vm.configuration_options.keys()
        if u'root' in keys: keys.remove(u'root')
        
        results = [] # configurations + results
        
        """ opt1;opt2;opt3;num1;nfp1;nfp2; """
        results.append(keys + self.nf_parameters)
        
        start = time.time()
        j = 1
        nr_runs = len(configurations) * N
        
        ptimer = ProcessTime(len(configurations))
        ptimer.start()
        
  
        conf_counter = 0
        
        for configuration in configurations:
            conf_counter += 1
           
           
            
            compiled_configuration = self.compile_configuration(configuration)
            compiled_configuration[u"MiB"] = "MiB"
            run = Template(self.build.project.run)
            bpath = self.build.build_target_path

            run_compiled = bpath + "/" + str(run.safe_substitute(compiled_configuration))

            """ Assesmble run command """
            tracked_parameters = " ".join(list(map(lambda f: '%'+f, self.nf_parameters))) + "' "
            
            command = "/usr/bin/time -f '" + tracked_parameters + run_compiled + " lab/" + benchmark_file + " " + benchmark_postfix
 
            print command
 
            now = time.time()
            duration_per_run = (now - start) / j
            
            seconds = duration_per_run*(nr_runs-j) 
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            left = "%dh %02dm %02ds" % (h, m, s)

            configuration_vector_b = self.compile_configuration_vector(binary_options, configuration)
            configuration_vector_n = self.compile_configuration_vector(numeric_options, configuration)
            configuration_vector = configuration_vector_b + configuration_vector_n
            
            resultso = []
            for i in range(N):
                j = j + 1
                
                self.reload_compression_task(benchmark_file)
                output = commands.getstatusoutput(command)[1]
                splitted = output.split('\n')[-1]
                output = list(map(lambda x: parse_number(x), splitted.split(' ')))
                
                resultso.append(output)
                
            medians = matrix_aggregate(resultso, len(self.nf_parameters), 'median') 
            mads = matrix_aggregate(resultso, len(self.nf_parameters), 'mad') 

            """
            Write performance data to file
            """
            with open(record_name, 'a') as f:
                writer = csv.writer(f)
                writer.writerow(configuration_vector + medians + mads)    
            
            #print configuration_vector + means
            
            ptimer.update()
            estimate = ptimer.estimate()
            m, s = divmod(estimate, 60)
            h, m = divmod(m, 60)

            #print "Configuration " + str(conf_counter) + " of " + str(len(configurations)) + ": Estimated time left is " + " %d:%02d:%02d" % (h, m, s)
            
        
    """
    Compiles a configuration dictionary (selection values are either boolean or numeric) with 
    to a dictionary of values to substitute in the run command template.
    """
    def compile_configuration(self, configuration): 
        compiled = {}
        
        
        
        for option in configuration.keys():
            
            if isinstance(configuration[option], bool):
                # Deselected options don't do anything
                if configuration[option] == False:
                    compiled[option] = ''
                    
                # Selected binary options are replaced with their respective output string from the variability model 
                else: # False
                    compiled[option] = self.vm.configuration_options[option].output_string
            
            else:
                # else: is numeric option
                # for numeric options compile their output string and the numeric value
                t_string = self.vm.configuration_options[option].output_string
                if t_string != None: template = Template( t_string.encode("utf-8") )
                if isinstance(configuration[option], bool):
                    compiled[option] = ""
                else:
                    s = str(configuration[option]).encode("utf-8")
                    compiliert = template.safe_substitute( n = s )
                    compiled[option] = compiliert
               
        # Return dictionary with compiled option values
        return compiled
    
    def compile_configuration_vector(self, keys, configuration):
        conf = []
        for key in keys:
            if key == "root":
                continue
            if isinstance(configuration[key], bool):
                if configuration[key]:
                    conf.append(1)
                else:
                    conf.append(0)
            else:
                conf.append(configuration[key])
        return conf
    
    
    def reload_compression_task(self, file):
        
        # remove any compression artifact in lab/
        os.system("rm -rf lab/*")
        #os.system("pwd")
        # copy the canterbury corpus to lab
        s = "cp  " + file + " lab/" + file
       #print s
        os.system(s)
