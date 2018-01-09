#!/usr/bin/env python
# -*- coding: utf-8 -*-

from splpioneer import PROJECT_BUILD_PATH, copy


import time
import os

"""
Wrapper class for any commit that can be build using the previously specified
build routine. Upon instantiation, the specified commit is checked out from the
cached repository and copied to a separate working directory for the 
respective commit / build.
"""
class Build:
    def __init__(self, project, hexsha):
        self.project = project
        self.hexsha = hexsha
        self.timestamp = list(filter(lambda c: c.hexsha == self.hexsha, self.project.commits))[0].committed_date
        self.build_target_path = PROJECT_BUILD_PATH(self.project.name, hexsha)
    """
    Creates a separate build directory for each commit unless the commit was 
    already checked out. Build the project according to the build routine in the
    project specification and leave a flag file with a last-built timestamp.
    """
    def build(self):
        """
        target = self.project.target
        repo = self.project.repository


        # ????????????????????????????????????????????????????????
        os.system("rm -rf " + self.build_target_path + "/*") # ????????
        # ????????????????????????????????????????????????????????


        # If the build working directory does not exist yet create one. 
        if not os.path.exists(self.build_target_path):
            os.makedirs(self.build_target_path)

        # Check out specified commit from the project's repository.
        repo.git.checkout(self.hexsha) 


        # Copy working directory to a separate build folder.
        copy(target, self.build_target_path + "/")


        # Apply build routine as specified in the project. Then leave a built timestamp and leave the directory. 
        
        #print "cd " + self.build_target_path + " && " + self.project.build
        os.system("cd " + self.build_target_path + " && " + self.project.build)
        
        with open(self.build_target_path + '/build.log','w') as f:

            f.write( str(time.time()) )
        """
    
    """
    Checks whether a build.log file exists in the build folder.
    """
    def built(self):
        os.path.isfile(self.build_target_path + '/build.log')
