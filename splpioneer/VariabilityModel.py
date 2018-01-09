from itertools import product, combinations
import xmltodict
import random

from splpioneer import xml_list
from splpioneer.ConfigurationOption import  ConfigurationOption
from numpy.compat.setup import configuration


class VariabilityModel:
    
    """
    Initializes variables representing the variability model from which the grammar can be constructed
    """
    def __init__(self, xml_path):
        self.path = xml_path 
        self.configuration_options = {} # list of features      
        
        self.ct_implications = [] # cross-tree implications
        self.ct_exclusions = [] # cross-tree exclusions
        
        self.excludes = {} # all exclusion rules including cross-tree ones
        self.alternative_groups = [] # alternative groups
        
        self.parents = {}
          
    """
    Parses the XML representation of the variability model.
    """
    def parse_vm(self):

        with open(self.path) as xml_file:
            vmxml = xmltodict.parse(xml_file.read())
                
            """
            The variability model ships with options as a list, so we have to assemble
            the tree structure by ourselves.
            1) Parse each option, binary and numeric ones
                """
            binaryOptions = xml_list(vmxml['vm']['binaryOptions'].values()[0])
            numericOptions = xml_list(vmxml['vm']['numericOptions'].values()[0])
                
                
            self.binaryOptions = []
            self.numericOptions = []
            #parents = {}
    
            """
            2) Parse a dictionary of exclusion rules. We have to split them to 
            a) alternative groups (sets of mutually exclusive options) and 
            b) cross-tree exclusions.
            """
            
            for binopt in binaryOptions:
    
                self.binaryOptions.append(binopt['name'])
    
                self.parents[binopt['name']] = binopt['parent']
    
                # type, name, output_string, parent, optional
                if binopt['optional'] == "True":
                    isOptional = True
                else:
                    isOptional = False
                    
                if binopt['children'] != None:
                    children = xml_list(binopt['children']['option'])
                else:
                    children = []
                conf_opt = ConfigurationOption('binary', binopt['name'], binopt['outputString'], binopt['parent'], isOptional,children)
    
                if binopt['excludedOptions'] != None:
                    exclds = xml_list( binopt['excludedOptions']['options'] )
                    self.excludes[ binopt['name'] ] = exclds
                     
                """ Look for implied options """
                if binopt['impliedOptions'] != None:
                    impls = xml_list( binopt['impliedOptions']['options'] )
                    for impl in impls:
                        self.ct_implications.append( (binopt['name'], impl) )
                    
                self.configuration_options[ binopt['name'] ] = conf_opt
                
            for numopt in numericOptions:
                
                self.numericOptions.append(numopt['name'])
                if 'parent' in numopt:
                    self.parents[numopt['name']] = numopt['parent']
                else:
                    self.parents[numopt['name']] = None
                    numopt['parent'] = None
    
                #name, output_string, parent, optional, implies=[], excludes=[]
                #print numopt['name']
                conf_opt = ConfigurationOption('numeric', numopt['name'], numopt['outputString'], numopt['parent'], False, [])
                if numopt['excludedOptions'] != None: 
                    exclds = xml_list( numopt['excludedOptions']['options'] )
                    self.excludes[ numopt['name'] ] = exclds
                        
                """ Look for implied options """
                if numopt['impliedOptions'] != None:
                    impls = xml_list( numopt['impliedOptions']['options'] )
                    for impl in impls:
                        self.ct_implications.append( (binopt['name'], impl) )
                   
                conf_opt.add_range( (numopt['minValue'], numopt['maxValue']) )
                x = numopt['stepFunction'].split('+')[-1]
                if '.' in x:
                    conf_opt.add_step( float(x) )
                else:
                    conf_opt.add_step( int(x) )
                self.configuration_options[ numopt['name'] ] = conf_opt
                
               
            # look for alternative groups
            for key in self.excludes.keys():
                if self.alternative_groups == [] or not any(list(map(lambda g: key in g, self.alternative_groups))):
                    self.alternative_groups.append( [key] + self.excludes[key] )
    
            # assert mutual exclusion for groups and extract ct-exclusions
            for key in self.excludes.keys():
                for e in self.excludes[key]:
                    if not e in self.excludes or not key in self.excludes[e]:
                        #exclusion is not mutual -> cross-tree constraint
                        self.ct_exclusions.append( (key, e) )
                            
                        for group in self.alternative_groups:
                            if key in group and e in group:
                                group.remove(e)
            self.alternative_groups = list(filter(lambda g: len(g) > 1, self.alternative_groups))
            
                        
    def build_grammar(self):
                
        grammar = {}
           
        """
        Add concrete selected Options for ConfigurationOptions
        """
        for conf_opt in self.configuration_options.keys():
            grammar[conf_opt] = self.configuration_options[conf_opt].get_configured()
        
        
        for i, group in enumerate(self.alternative_groups):
                
            # Assert that all options in one group have the same parent option 
            assert len(set( list(map(lambda o: self.parents[o], group)) )) <= 1
            
            """
            This parent must be the parent production rule for all members 
            """
            nt_new = self.parents[group[0]]
            
            productions = list(map(lambda o: set([o]), group))
            for p in productions:
                p.add( (nt_new, True) )
            grammar[nt_new] = productions

        #if 'root' in grammar.keys(): 
        #del grammar['root']
        
        # return Grammar instance
        return Grammar(grammar, self.ct_exclusions, self.ct_implications, self.configuration_options, self.binaryOptions, self.numericOptions)   
    
class Grammar:
    def __init__(self, grammar, exclusions, implications, conf_opts, binopts, numopts):
        self.grammar = grammar
        self.ct_exclusions = exclusions
        self.ct_implications = implications
        self.configuration_options = conf_opts
        self.binaryOptions = binopts
        self.numericOptions = numopts
        
    def expand(self):
        
        grammar = self.grammar
        
        """ 
        All features with no explicit parent are the entry point for
        grammar expansion. Unless a non-terminal can be accessed from 
        another production, our start configuration (of non-terminals)
        includes the left side of each production
        """
        start = set(grammar.keys()) 
        nts_from_productions = set([])
        for key in grammar:
            for production in grammar[key]:
                from_productions = list(filter(lambda x: isinstance(x, unicode), production))
                nts_from_productions = nts_from_productions | set(from_productions)
        start = start - nts_from_productions

        """
        Grammar expansion starts with a set of non-terminals that will
        be eliminated one after another. 
        Once, if a word (i.e., set) only contains terminal symbols 
        (i.e., Option instances), the word is yielded. Otherwise, the 
        word still contains non-terminal to be eliminated.
        """
        queue = [start]
        while len(queue):
            current = queue.pop(0)
            
            """ if a word does not conform to ct-constraints -> stop expansion for that word"""
            if not self.conforms_to_ctcs(current):
                continue
            
            for key in grammar:  # F, Z, X1, X2
                if (key in current): # current = set, key in set?
                    # replace non-terminal with terminal symbol
                    for production in grammar[key]: # production = set
                        new = current.copy() # new = copied word current
                        new.remove(key) # remove key from set 
                        new = new | production 
                        if (not any(key for key in grammar if key in new)):
                            yield new
                        else:
                            queue.append(new)
                    break
                
    def get_all_configurations(self):
        configurations = [conf for conf in self.expand()]
        already_configured = lambda cfg: set(list(map(lambda o: o[0], cfg)))
        
        configurations_as_dicts = []
        for c in configurations:
            already_configured_features = already_configured(c) 
            not_configured_features = set(self.configuration_options.keys()) - already_configured_features
            
            configuration = {}
            for f in not_configured_features:
                configuration[f] = False
            for o in c:
                configuration[o[0]] = o[1]
                
            if u'root' in configuration: del configuration['root']
            configurations_as_dicts.append(configuration)
        
        return configurations_as_dicts
    
    def conforms_to_ctcs(self, word):
        satisfieds = [] # are all constraints satisfied?
        
        # check cross-tree exclusions
        for constraint in self.ct_exclusions:
            a = constraint[0]
            b = constraint[1]
            satisfied = not (a, True) in word or not (b, True) in word # A => !B ~ !A or !B
            satisfieds.append(satisfied)
        
        # check cross-tree implications
        for constraint in self.ct_implications:
            a = constraint[0]
            b = constraint[1]
            satisfied = not (a, True) in word or (b, True) in word # A => B ~ !A or B
            satisfieds.append(satisfied)
            
        return all(satisfieds)
    
    def copy(self):
        return Grammar(self.grammar, self.ct_exclusions, self.ct_implications, self.configuration_options, self.binaryOptions, self.numericOptions)
    
    def genBinaryPartialConfigs(self):
        copy = self.copy()
        for numopt in self.numericOptions:
            del copy.grammar[numopt]
            copy.numericOptions = []
        f = copy.get_all_configurations()
        configs = []
        for conf in f:
            d = conf
            if u'D' in d: del d[u'D']
            if u'N' in d: del d[u'N']
            configs.append(d)
        return configs
    
    def genNumericPartialConfigs(self, n):
        
        random.seed(42)
        
        domain_of = {}
        for numopt in self.numericOptions:
            domain_of[numopt] = self.grammar[numopt]
        
        partial_configurations = []
        for i in range(n):
            conf = dict()
            for numopt in domain_of.keys():
                index = random.randint(0, len(domain_of[numopt]) - 1)
                conf[numopt] = list(domain_of[numopt][index])[0][1]
            partial_configurations.append(conf)
        return partial_configurations
        
    def sampleTWise(self, t, n):
        
        numeric_partial_configurations = self.genNumericPartialConfigs(n)
        
        if u'root' in self.binaryOptions: self.binaryOptions.remove(u'root')
        binary_pairs = list(combinations(self.binaryOptions, t))
        binary_pairs_dict = {}
        for pair in binary_pairs:
            binary_pairs_dict[pair] = False
        #print binary_pairs
        all_binary_partials = self.genBinaryPartialConfigs()

        filtered_binary_partialz = []
        for tupel in binary_pairs:
            for i, binary_conf in enumerate(all_binary_partials):
                contains_tupel = binaryAndFold( list(map(lambda x: binary_conf[x], tupel)))
                
                
                if contains_tupel and not binary_pairs_dict[tupel] and len(filtered_binary_partialz) < len(all_binary_partials):
                    binary_pairs_dict[tupel] = True
                    
                    # TODO this should not be 
                    if u'N' in binary_conf: del binary_conf[u'N']
                    if u'D' in binary_conf: del binary_conf[u'D']
                    
                    filtered_binary_partialz.append(i)
        
        filtered_binary_partialz = list(set(filtered_binary_partialz))
                    
        print filtered_binary_partialz, len(filtered_binary_partialz)
        filtered_binary_partials = []
        for index in filtered_binary_partialz:
            filtered_binary_partials.append(all_binary_partials[index])
        sample_configurations = []
        
        j = 0
        for binconf in filtered_binary_partials:
            for numconf in numeric_partial_configurations:
                j += 1
                new = dict(binconf.items() + numconf.items())
                sample_configurations.append(new)
                
        return sample_configurations
    
def binaryAndFold(bs):
    t = True
    for b in bs:
        t = t and b
    return t
    
def binaryOrFold(bs):
    t = False
    for b in bs:
        t = t or b  
    return t  
        