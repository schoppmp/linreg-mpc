from matplotlib import rc, pyplot as plt
import numpy as np
import os
import sys
from itertools import cycle
import scikits.bootstrap

# ranges of input parameters
ds = [10, 20, 50, 100, 200, 500]
ns = [100000]#[1000, 2000, 5000, 100000, 500000]
algos = ['cholesky', 'cgd']

# constants (but can be changed in the future)
sigma = 0.1
num_samples = 3
num_iterations = 15
dirname = "../experiments/results/phase2_time"

# n x d x sample x algo -> (condition_number, objective, ot_time, time, error, circuit_size)
data = np.ndarray(shape=(len(ns), len(ds), num_samples, len(algos), 6))
data[:] = np.NAN

# n x d x sample x iteration -> (error, objective, time, circuit_size)
data2 = np.ndarray(shape=(len(ns), len(ds), num_samples, num_iterations, 4))
data2[:] = np.NAN

for i_n, n in enumerate(ns):
    for i_d, d in enumerate(ds):
        for i_algo, algo in enumerate(algos):
            for sample in xrange(num_samples):
                outfile = "test_LS_{}x{}_{}_{}_{}_{}_p2.out".format(n, d, sigma, sample, algo, num_iterations)
                try: 
                    lines = open(os.path.join(dirname, outfile), 'r').read().splitlines()
                    index_cond = lines.index("Condition number:") + 1
                    fields = lines[1].split()[3:]
                    if len(fields) == 3: 
                        data[i_n, i_d, sample, i_algo, [0,3,4,5]] = np.array([lines[index_cond]] 
                                                                             + fields, 
                                                                             dtype=np.float64)
                    elif len(fields) == 4:
                        index_obj = lines.index("Objective function on solution:") + 1
                        data[i_n, i_d, sample, i_algo, :] = np.array([lines[index_cond]] 
                                                                     + [lines[index_obj]]
                                                                     + fields,
                                                                     dtype=np.float64)
                    else:
                        print "Invalid line: {} in file {}".format(lines[1], outfile)
                    if algo == 'cgd':
                        for i_line, line in enumerate(lines[3:3+num_iterations]):
                            fields = line.split()[1:]
                            if len(fields) == 2: # old version without objective, time
                                data2[i_n, i_d, sample, i_line, [0, 3]] = np.array(fields, dtype=np.float64)
                            elif len(fields) == 4: # new version 
                                data2[i_n, i_d, sample, i_line, :] = np.array(fields, dtype=np.float64)
                            else:
                                print "Invalid line: {} in file {}".format(line, outfile)
                except IOError, e:
                    print e
                    pass

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
indices_cgd = [4, 9, 14]
mean_size_cholesky = np.nanmean(data[:,:,:,0,5], axis=(0, 2))
mean_size_cgd = np.nanmean(data2[:,:,:,:,3], axis=(0, 2))

colours = ['#404096', '#57a3ad', '#dea73a', '#d92120']
colourcycler = cycle(colours)

plt.xscale('log')
plt.xlabel('$d$')
plt.xticks(ds, ["${}$".format(d) for d in ds]) # axes in mathmode
plt.yscale('log')
plt.ylabel('Circuit size (gates)')
plt.plot(ds, mean_size_cholesky, marker='.', c=next(colourcycler))#, yerr=std_size_cholesky)
for i in indices_cgd:
    plt.plot(ds, mean_size_cgd[:,i], marker='.', c=next(colourcycler))#, yerr=std_cgd[:,i])
plt.legend(["Cholesky"] + ["CGD {}".format(index + 1) for index in indices_cgd], loc=2)
plt.tight_layout()
plt.savefig("plot_circuit_size.pdf", transparent=True)
plt.show()

# plot 2: d -> time, compare cgd and cholesky
indices_cgd = [4, 9, 14]

# compute confidence intervals for each value of n, d and each iteration
cis_cgd = np.ndarray(shape=(len(ds), num_iterations, 2))
cis_cholesky = np.ndarray(shape=(len(ds), 2))
cis_ot = np.ndarray(shape=(len(ds), 2))
for i_d in xrange(len(ds)):
    for iteration in xrange(num_iterations):
        data_flat = data2[:, i_d, :, iteration, 2].flat
        cis_cgd[i_d, iteration] = scikits.bootstrap.ci(data_flat, method="abc")
    data_flat=data[:, i_d, :, 0, 3].flat
    cis_cholesky[i_d] = scikits.bootstrap.ci(data_flat, method="abc")
    cis_ot[i_d] = scikits.bootstrap.ci(data[:,i_d,:,:,2].flat, method="abc")
    

mean_time_cholesky = np.mean(data[:,:,:,0,3], axis=(0, 2))
mean_time_cgd = np.mean(data2[:,:,:,:,2], axis=(0, 2))
mean_time_ot = np.mean(data[:,:,:,:,2], axis=(0,2,3))

plt.xscale('log')
plt.xlabel('$d$')
plt.xticks(ds, ["${}$".format(d) for d in ds]) # axes in mathmode
plt.yscale('log')
plt.ylabel('Time (seconds)')

yerr = [mean_time_cholesky - cis_cholesky[:,0], cis_cholesky[:,1] - mean_time_cholesky]
plt.errorbar(ds, mean_time_cholesky, marker='.', yerr=yerr, c=next(colourcycler))
for i in indices_cgd:
    yerr = [mean_time_cgd[:,i] - cis_cgd[:,i,0], cis_cgd[:,i,1] - mean_time_cgd[:,i]]
    plt.errorbar(ds, mean_time_cgd[:,i], marker='.', yerr=yerr, c=next(colourcycler))
yerr = [mean_time_ot - cis_ot[:,0], cis_ot[:,1] - mean_time_ot]
plt.errorbar(ds, mean_time_ot, marker='.', linestyle=":", yerr=yerr, c='#000000')
plt.legend(["Cholesky"] + ["CGD {}".format(index + 1) for index in indices_cgd] + ["OT"], loc=2)
plt.tight_layout()
plt.savefig("plot_time_phase2.pdf", transparent=True)
plt.show()

for i_d, d in enumerate(ds):
        sys.stdout.write("{:<10d}".format(d))
        sys.stdout.write("& {:9.3f} ".format(mean_time_ot[i_d]))
        sys.stdout.write("& {:9.3f} ".format(mean_time_cholesky[i_d]))
        for i, idx in enumerate(indices_cgd):
            sys.stdout.write("& {:9.3f} ".format(mean_time_cgd[i_d,idx]))
        sys.stdout.write("\\\\\n")
