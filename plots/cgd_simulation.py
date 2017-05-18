import numpy as np
from matplotlib import rc, pyplot as plt
import scipy.io
from itertools import cycle

mat = scipy.io.loadmat("../experiments/matlab/test9.mat")

# set pyplot look
rc('text', usetex=True)
rc('text.latex', preamble='\usepackage{lmodern}')
rc('lines', linewidth=1)
rc('patch', linewidth=1)
rc('axes', linewidth=1)
rc('figure',  figsize=(2.5, 2.5))
rc('savefig', format='pdf')

bits = 64
fbs = [55,54,53,52,0];

colours = ['#404096', '#57a3ad', '#dea73a', '#d92120', '#000000']
colourcycler = cycle(colours)

# textbook CGD
plt.xlabel('CGD Iteration $t$')
plt.yscale('log')
plt.ylabel('Residual $\\|A \\theta_t - b\\|$')
plt.xlim([1,50])
plt.ylim([1e-18, 0.01])
for i in range(len(fbs)):
    data = mat["terr"][0][i][0]
    plt.plot(range(1,len(data)+1), data, c=next(colourcycler))
plt.savefig("cgd_simulation_textbook.pdf", transparent=True, bbox_inches='tight')
plt.show()

# FP-CGD
plt.xlabel('CGD Iteration $t$')
plt.yscale('log')
plt.ylabel('Residual $\\|A \\theta_t - b\\|$')
plt.xlim([1,50])
plt.ylim([1e-18, 0.01])
for i in range(len(fbs)):
    data = mat["ferr"][0][i][0]
    plt.plot(range(1,len(data)+1), data, c=next(colourcycler))
plt.legend(["$b_i = {}$".format(bits - b_f - 1) for b_f in fbs[:-1]] + ["Float"], loc=1)
plt.savefig("cgd_simulation_fixed.pdf", transparent=True, bbox_inches='tight')
plt.show()
