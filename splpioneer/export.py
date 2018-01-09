import sqlite3 as sql
import csv
from string import Template
from numpy.compat.setup import configuration
from splpioneer import kpis

def export(project, revision, timestamp, file = 'export.csv'):
    
    # Retrieve all configurations
    conn = sql.connect('../database.db')
    c = conn.cursor()
    command_t = Template("SELECT * FROM Configuration WHERE revision = '$rev' AND timestamp = $time")
    command = command_t.safe_substitute(rev = revision, time = timestamp)
    c.execute(command)
    conn.commit()
    
    configurations = []
    for row in c:
        configurations.append(row[0])
    
    conn.close()
    
    # list all binary and numeric features
    binary_features = []
    numeric_features = []
    
    conn = sql.connect('../database.db')
    c = conn.cursor()
    command_binary = Template("SELECT name FROM BinaryFeature WHERE project = '$project' ORDER BY name COLLATE NOCASE ASC")
    command = command_binary.safe_substitute(project = project)
    c.execute(command)
    for row in c:
        binary_features.append(row[0])
    conn.commit()
    conn.close()
    
    conn = sql.connect('../database.db')
    c = conn.cursor()
    command_binary = Template("SELECT name FROM NumericFeature WHERE project = '$project' ORDER BY name COLLATE NOCASE ASC")
    command = command_binary.safe_substitute(project = project)
    c.execute(command)
    for row in c:
        numeric_features.append(row[0])
    conn.commit()
    conn.close()
    
    binary_features.remove(u'root')
    features = binary_features + numeric_features
    
    # per configuration, record all binary and numeric values
    values_binary_t = Template("SELECT feature, value FROM ConfiguredBinaryFeature WHERE feature IN (SELECT name FROM BinaryFeature WHERE project = '$project') AND ConfiguredBinaryFeature.revision = '$rev' AND timestamp = $time AND configuration = $config")
    values_numeric_t = Template("SELECT feature, value FROM ConfiguredNumericFeature WHERE feature IN (SELECT name FROM NumericFeature WHERE project = '$project') AND ConfiguredNumericFeature.revision = '$rev' AND timestamp = $time AND configuration = $config")

    values_per_configuration = {}
    for configuration in configurations:
        
        binary_values_tuples = []
        conn = sql.connect('../database.db')
        c = conn.cursor()
        command = values_binary_t.safe_substitute(project = project, rev = revision, time = timestamp, config = configuration)
        c.execute(command)
        for row in c:
            binary_values_tuples.append(row)
        conn.commit()
        values_binary = tuples2dict( binary_values_tuples )
        conn.close()
        
        numeric_values_tuples = []
        conn = sql.connect('../database.db')
        c = conn.cursor()
        command = values_numeric_t.safe_substitute(project = project, rev = revision, time = timestamp, config = configuration)
        c.execute(command)
        for row in c:
            numeric_values_tuples.append(row)
        conn.commit()
        conn.close()
        values_numeric = tuples2dict( numeric_values_tuples )
        
        values =  list(map(lambda f: 1 if values_binary[f] == u'True' else 0, binary_features)) + list(map(lambda f: values_numeric[f], numeric_features))     
            
        values_per_configuration[configuration] = values
        conn.close()
        
    for configuration in configurations:
        measurements = []
        
        for kpi in kpis:
            
            conn = sql.connect('../database.db')
            c = conn.cursor()
            command = Template("SELECT mean FROM record_{$kpi} WHERE revision = '$revision' AND timestamp = $timestamp AND id = $id")
            command = command.safe_substitute(revision = revision, timestamp = timestamp, id = configuration, kpi = kpi).replace("{","").replace("}","")
            c.execute(command)
            for row in c:
                measurements.append(row[0])
                break
            conn.commit()
            conn.close()

        values_per_configuration[configuration] = values_per_configuration[configuration] + measurements
        
    with open(file, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(features + kpis)
        for i in values_per_configuration:
            writer.writerow(values_per_configuration[i])

def tuples2dict(ts):
    out = dict()
    for t in ts:
        out[t[0]] = t[1]
    return out
    
