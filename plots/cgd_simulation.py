import numpy as np
from matplotlib import rc, pyplot as plt
import scipy.io
from itertools import cycle

mat = scipy.io.loadmat("experiments/matlab/test9.mat")

# set pyplot look
rc('text', usetex=True)
rc('text.latex', preamble='\usepackage{lmodern}')
rc('lines', linewidth=1)
rc('patch', linewidth=1)
rc('axes', linewidth=1)
rc('figure', figsize=(9, 6))
#rc('errorbar', capsize=5)
rc('savefig', format='pdf')

# plot 1: d -> size, compare cgd{5,10,15} and cholesky
bits = 64
fbs = [55,54,53,52,0];

colours = ['#404096', '#57a3ad', '#dea73a', '#d92120', '#000000']
colourcycler = cycle(colours)

plt.xlabel('CGD Iterations')
plt.yscale('log')
plt.ylabel('Residual')
plt.xlim([1,50])
for i in range(len(fbs)):
    data = mat["terr"][0][i][0]
    plt.plot(range(1,len(data)+1), data, marker='.', c=next(colourcycler))#, yerr=std_cgd[:,i])
plt.legend(["$b_i = {}$".format(bits - b_f - 1) for b_f in fbs[:-1]] + ["Floating Point"], loc=1)
plt.tight_layout()
plt.savefig("cgd_simulation_textbook.pdf", transparent=True)
plt.show()

plt.xlabel('CGD Iterations')
plt.yscale('log')
plt.ylabel('Residual')
plt.xlim([1,50])
for i in range(len(fbs)):
    data = mat["ferr"][0][i][0]
    plt.plot(range(1,len(data)+1), data, marker='.', c=next(colourcycler))#, yerr=std_cgd[:,i])
plt.legend(["$b_i = {}$".format(bits - b_f - 1) for b_f in fbs[:-1]] + ["Floating Point"], loc=1)
plt.tight_layout()
plt.savefig("cgd_simulation_fixed.pdf", transparent=True)
plt.show()
