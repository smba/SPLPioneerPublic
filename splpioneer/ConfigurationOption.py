from splpioneer import frange

"""
Wrapper class for configuration options for the XML parser
"""
class ConfigurationOption:
    
    def __init__(self, typ, name, output_string, parent, optional, children, implies=[], excludes=[]): # TODO add more args
        self.typ = typ
        self.name = name
        self.output_string = output_string
        self.parent = parent
        self.implies = implies
        self.excludes = excludes
        self.optional = optional
        self.children = children
    
    def add_range(self, minmax):
        self.min = int(minmax[0])
        self.max = int(minmax[1])
    
    def add_step(self, step):
        self.step = step
        
    def get_configured(self):
        if self.typ == 'numeric':
            configured = []
            for i in frange(self.min, self.max, self.step):
                configured.append( set([ (self.name, i) ]) )
            return configured
        
        elif self.typ =='binary':
            children = set([])
            if len(self.children) > 0:
                children = set(self.children)
            selected = (self.name, True)
            if self.optional:
                return [set([selected]) | children, set([(self.name, False)])]
            else:
                ex = set([selected]) | children
                return [ex]  