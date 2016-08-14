from matplotlib import rc, pyplot as plt
import numpy as np
import glob
import os
from itertools import cycle

dirname = "../experiments/results/phase2_scatter_data"
files_cgd = glob.glob(os.path.join(dirname, "*_cgd_*.out"))
num_iterations = 15
# file x iteration -> (error, objective)
data_cgd = np.ndarray(shape=(len(files_cgd), num_iterations, 2))
data_cgd[:] = np.NAN
# file -> condition number
condition_numbers_cgd = np.ndarray(shape=(len(files_cgd)))
condition_numbers_cgd[:] = np.NAN
for i_f, filename in enumerate(files_cgd):
    lines = open(filename).read().splitlines()
    condition_numbers_cgd[i_f] = lines[-1]
    for iteration in xrange(num_iterations):
        data_cgd[i_f, iteration, 0:2] = lines[3+iteration].split()[1:3]

files_cholesky = glob.glob(os.path.join(dirname, "*_cholesky_*.out"))
num_iterations = 15
# file x iteration -> (error, objective)
data_cholesky = np.ndarray(shape=(len(files_cholesky)))
data_cholesky[:] = np.NAN
# file -> condition number
condition_numbers_cholesky = np.ndarray(shape=(len(files_cholesky)))
condition_numbers_cholesky[:] = np.NAN
for i_f, filename in enumerate(files_cholesky):
    lines = open(filename).read().splitlines()
    condition_numbers_cholesky[i_f] = lines[-1]
    data_cholesky[i_f] = lines[1].split()[5]

        
# set pyplot look
rc('text', usetex=True)
rc('text.latex', preamble='\usepackage{lmodern}')
rc('lines', linewidth=1)
rc('patch', linewidth=1)
rc('axes', linewidth=1)
rc('figure', figsize=(9,6))
#rc('errorbar', capsize=5)
rc('savefig', format='pdf')

ax = plt.gca()
symbols = ["x"]

colours = ['#404096', '#57a3ad', '#dea73a', '#d92120']
colourcycler = cycle(colours)
symbolcycler = cycle(symbols)
#next(colourcycler)
#next(symbolcycler)
iters=[4,9,14]
ax.scatter(condition_numbers_cholesky, data_cholesky, c=next(colourcycler), marker=next(symbolcycler))
for iteration in iters:
   ax.scatter(condition_numbers_cgd, data_cgd[:,iteration,0], c=next(colourcycler), marker=next(symbolcycler))
ax.set_yscale('log')
#ax.set_xscale('log')
ax.set_xlim([1,11])
ax.set_ylim([1e-18, 1])
plt.legend(["Cholesky"] + ["CGD {}".format(i+1) for i in iters], loc=4)
plt.ylabel(r"Error")
plt.xlabel(r"Condition Number $\kappa$")
plt.tight_layout()
plt.savefig("plot_scatter.pdf", transparent=True)
plt.show()
