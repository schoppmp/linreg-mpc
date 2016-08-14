from matplotlib import rc, pyplot as plt
import numpy as np
import os
import sys
from itertools import cycle
import scikits.bootstrap

# ranges of input parameters
ds = [10, 20, 50, 100, 200, 500]
ns = [100000]
algos = ['cgd']

# constants (but can be changed in the future)
sigma = 0.1
num_samples = 30
num_iterations = 15
dirname = "../experiments/results/phase2_accuracy/"

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
rc('figure', figsize=(9,6))
#rc('errorbar', capsize=5)
rc('savefig', format='pdf')


colours = ['#1965b0', '#7bafde', '#4eb265', '#cae0ab', '#f6c141', '#dc050c']

# plot 3: iteration -> error, compare ds
# compute confidence intervals for each value of d and each iteration
cis = np.ndarray(shape=(len(ds), num_iterations, 2))
for i_d in xrange(len(ds)):
    for iteration in xrange(num_iterations):
        cis[i_d, iteration] = scikits.bootstrap.ci(data2[:, i_d, :, iteration, 0].flat, method='abc')

colourcycler = cycle(colours)
mean_error = np.nanmean(data2[:,:,:,:,0], axis=(0, 2))
std_error = np.nanstd(data2[:,:,:,:,0], axis=(0, 2))
plt.xlabel('Iteration')
plt.yscale('log')
plt.ylabel('Error')
plt.xlim((1,num_iterations))
plt.xticks(range(1,num_iterations+1))
for i, d in enumerate(ds):
    yerr=[mean_error[i,:] - cis[i,:,0], cis[i,:,1]-mean_error[i,:]]
    plt.errorbar(xrange(1, num_iterations+1), mean_error[i,:], yerr=yerr, c=next(colourcycler))
plt.legend(["d = {}".format(d) for d in ds])
plt.tight_layout()
plt.savefig("plot_accuracy_cgd.pdf", transparent=True)
plt.show()

# plot 4: iteration -> abs(obj(iteration) - obj) / obj
#obj_solution = data[:,:,:,np.newaxis,1,1]
#mean_error = np.nanmean(np.abs(data2[:,:,:,:,1] - obj_solution) / obj_solution , axis=(0,2))
colourcycler = cycle(colours)
obj_solution = data[:,:,:,np.newaxis,0,1]
rel_error = np.abs(data2[:,:,:,:,1] - obj_solution) / obj_solution
mean_error = np.nanmean(rel_error, axis=(0,2))

cis = np.ndarray(shape=(len(ds), num_iterations, 2))
for i_d in xrange(len(ds)):
    for iteration in xrange(num_iterations):
        cis[i_d, iteration] = scikits.bootstrap.ci(rel_error[:, i_d, :, iteration].flat, method='abc')
            
std_error = np.nanstd(rel_error, axis=(0,2))
plt.xlabel('Iteration')
plt.yscale('log')
plt.ylabel('Error')
plt.xlim((1,num_iterations))
plt.xticks(range(1,num_iterations+1))
for i, d in enumerate(ds):
    yerr = [mean_error[i,:] - cis[i,:,0], cis[i,:,1]-mean_error[i,:]]
    plt.errorbar(xrange(1, num_iterations+1), mean_error[i,:], yerr=yerr, c=next(colourcycler))
plt.legend(["d = {}".format(d) for d in ds])
plt.tight_layout()
plt.savefig("plot_accuracy_cgd2.pdf", transparent=True)
plt.show()

print "Average condition number: {}".format(np.mean(data[:,:,:,:,0]))
