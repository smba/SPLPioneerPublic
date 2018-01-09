import sqlite3 as sql
from string import Template
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt

# retrieve all commit sizes for xz
conn = sql.connect('../database.db')
c = conn.cursor()
command = Template("SELECT mean FROM record_throughput_O")
command = command.safe_substitute(project = 'xz')
c.execute(command)
    
xs = []
for row in c:
    xs.append(row[0])
    
conn.commit()

# Fit a normal distribution to the data:
mu, std = norm.fit(xs)

# Plot the histogram.
plt.hist(xs, bins=25, alpha=0.6, color='gray', normed=True, histtype='step')

#plot norm
xmin, xmax = plt.xlim()
x = np.linspace(xmin, xmax, 100)
p = norm.pdf(x, mu, std)
plt.plot(x, p, 'k', linewidth=2)

plt.show()


print mu, std