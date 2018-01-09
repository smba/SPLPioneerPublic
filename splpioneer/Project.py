#!/usr/bin/env python
# -*- coding: utf-8 -*-
from nbformat import current


""" Resources folder for the application """

import errno
import os
import shutil
from string import Template
import json
import git

import sqlite3 as sql


RESOURCES = os.getcwd() + "/resources"

""" Path to the Git repository of a project """
PROJECT_PATH = lambda name: RESOURCES + "/" + name + "/repository"

""" Path to the build directory of project """
PROJECT_BUILD_PATH = lambda name: RESOURCES + "/" + name + "/build"


class Project:
    def __init__(self, name, remote="", build="", run=""):
        
        conn = sql.connect('database.db')
        c = conn.cursor()

        contains = Template("SELECT * FROM Project WHERE name = '$name'").safe_substitute(name=name)
        c.execute(contains)
        
        fetched_one = c.fetchone()
        
        conn.commit()
        conn.close()
        conn2 = sql.connect('database.db')
        c = conn2.cursor()
        
        
        if fetched_one == None: # noch nicht in der Datenbank enthalten
            
            # insert project in database
            insert_template = Template("INSERT INTO Project VALUES ('$name', '$remote', '$build', '$run')")
            insert_template_substituted = insert_template.safe_substitute(name=name, remote=remote, build=build, run=run)
            c.execute(insert_template_substituted)
            
            # set paramaters
            self.name = name
            self.remote = remote
            self.build = build
            self.run = run
            
        else:
            self.name = fetched_one[0]
            self.remote = fetched_one[1]
            self.build = fetched_one[2]
            self.run = fetched_one[3]
                
        conn2.commit()
        conn2.close()
                
        # now, clone the repository
        # (expected) target path, i.e., where to store the repository
        self.target = PROJECT_PATH(self.name)
  

        # do we already have a copy of that? If not clone the specified repository
        if not os.path.exists(self.target):
            self.repository = git.Repo.clone_from(self.remote, self.target)
            self.commits = list(self.repository.iter_commits('master', max_count = -1))
            
            inserts = []
            i = 0
            for commit in self.commits:
                i = i + 1
                #inserted = 0
                #deleted = 0
                #for file_name in commit.stats.files.keys():
                #    inserted += commit.stats.files[file_name]["insertions"]
                #    deleted += commit.stats.files[file_name]["deletions"]
    
                template = Template("('$id', '$project', '$timestamp', '$message', '$lines_added', '$lines_deleted')")
                
                message = commit.message.replace("'","").replace('"','')
                
                templated = template.safe_substitute(
                    id = commit.hexsha,
                    project = self.name,
                    timestamp = commit.committed_date,
                    message = message,
                    lines_added = 0,#inserted,
                    lines_deleted = 0#deleted
                )
                
                conn3 = sql.connect('database.db')
                c = conn3.cursor()
                
                command = "INSERT INTO Revision VALUES " + templated
                c.execute(command)
            
                conn3.commit()
                conn3.close()
            
        else:
            self.repository = git.Repo(self.target) 
            self.commits = list(self.repository.iter_commits('master', max_count = -1))
            
    def sampleCommitCoverage(self, coverage, max_commits):
        # retrieve all commit sizes for xz
        conn = sql.connect('database.db')
        c = conn.cursor()
        command = Template("SELECT * FROM Revision WHERE project = '$project'")
        command = command.safe_substitute(project = self.name)
        c.execute(command)
        
        timestamps = []
        time_to_next = []
        for row in c:
            timestamps.append( (row[0], row[2]) )       
        conn.commit()

        for i in xrange(1, len(timestamps)):
            time_to_next.append( (timestamps[i][0], timestamps[i - 1][1] - timestamps[i][1]) )
            
        total_duration = timestamps[0][1] - timestamps[-1][1]
        time_to_next.sort(key=lambda tupel: tupel[1], reverse = True)
        
        covered = 0
        i = 0
        revisions = []
        while len(revisions) < max_commits and 1.0*covered / total_duration < coverage:
            covered += time_to_next[i][1]
            revisions.append(time_to_next[i][0])
            i += 1
        
        return (len(revisions), 1.0*covered / total_duration)
    
    def sampleReleaseCommits(self):
        conn = sql.connect('database.db')
        c = conn.cursor()
        command = Template("SELECT * FROM Revision WHERE project = '$project'")
        command = command.safe_substitute(project = self.name)
        c.execute(command)
        
        timestamps = []
        time_to_next = []
        for row in c:
            timestamps.append( (row[0], row[2]) )       
        conn.commit()
        
        for i in xrange(1, len(timestamps)):
            time_to_next.append( (timestamps[i][0], timestamps[i - 1][1] - timestamps[i][1]) )
            
        total_duration = timestamps[0][1] - timestamps[-1][1]
        
        # get rleases
        conn = sql.connect('database.db')
        d = conn.cursor()
        command = Template("SELECT * FROM Release WHERE project = '$project'")
        command = command.safe_substitute(project = self.name)
        d.execute(command)
        
        releases = []
        for release in d:
            releases.append( row[0] )

        covered = 0
        for (rev, tonext) in time_to_next:
            if rev in releases:
                covered += tonext
        
        return (len(releases), 1.0*covered/total_duration)
    
    def getCommits(self):
        f = []
        for commit in self.commits:
            f.append(commit.hexsha)
        return f