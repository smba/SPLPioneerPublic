import numpy as np
import matplotlib as plt
import sqlite3 as sql
from string import Template
import matplotlib.pyplot as plt

def plot_commit_sizes(project, log=False, releases=True):
        # retrieve all commit sizes for xz
    conn = sql.connect('../database.db')
    c = conn.cursor()
    command = Template("SELECT * FROM Revision WHERE project = '$project'")
    command = command.safe_substitute(project = project)
    c.execute(command)
    
    xs = []
    ys = []
    for row in c:
        xs.append(row[2])
        ys.append(row[4]+row[5])
    
    conn.commit()
    conn.close()
    
    #zs = sorted(zs, key=lambda x: x[1], reverse = True)
    plt.scatter(xs, ys, marker = '.', color='black', alpha = 0.75, s = 20)
    plt.xlabel('commit commit [ms]')
    plt.ylabel('lines modified [loc]')
    plt.title("Commit sizes / commit time for '" + project + "'")
    
    rxs = []
    rys = []
    if releases:
        conn = sql.connect('../database.db')
        c = conn.cursor()
        command = Template("SELECT * FROM Release WHERE project = '$project'")
        command = command.safe_substitute(project = project)
        c.execute(command)
        
        for row in c:
            rxs.append(row[2])
            rys.append(0)
        
        conn.commit()
        conn.close()
    plt.scatter(rxs, rys, marker = 's', color='green', alpha = 0.75, s = 30)
        
    
    if log:
        plt.yscale('log', nonposy='clip')
    #plt.axis([40, 160, 0, 0.03])
    plt.grid(True)
    plt.show()

def plot_commit_differences(project, log=False):
    # retrieve all commit sizes for xz
    conn = sql.connect('../database.db')
    c = conn.cursor()
    command = Template("SELECT * FROM Revision WHERE project = '$project'")
    command = command.safe_substitute(project = project)
    c.execute(command)
    
    xs = []
    ys = []
    for row in c:
        xs.append(row[2])
        ys.append(row[4]+row[5])
    
    conn.commit()
    
    zs = [] # time until next commit
    for i in xrange(1, len(xs)):
        zs.append(xs[i - 1] - xs[i])
        
    #zs = sorted(zs, key=lambda x: x[1], reverse = True)
    plt.hist(zs, alpha=0.75)
    plt.xlabel('time to next commit [ms]')
    plt.ylabel('frequency')
    plt.title("Histogram of time between two commits for '" + project + "'")
    
    if log:
        plt.yscale('log', nonposy='clip')
    #plt.axis([40, 160, 0, 0.03])
    plt.grid(True)
    plt.show()
    
for p in ['tar', 'x264', 'xz']:
    #plot_commit_differences(p, True)
    plot_commit_sizes(p, False)