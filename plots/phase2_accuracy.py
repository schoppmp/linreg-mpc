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
num_samples = 2
num_iterations = 20

for bw in [32, 64]:
    if bw == 64:
        dirname = "../experiments/results/phase2_64"
    else:
        dirname = "../experiments/results/phase2_32"

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
                    outfile = "test_LS_{}x{}_{}_{}_{}_{}_{}_p2.out".format(n, d, sigma, sample, algo, bw, num_iterations)
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
    rc('figure', figsize=(4.5, 3))
    rc('errorbar', capsize=5)
    rc('savefig', format='pdf')

    # plot: d -> error, compare cgd{5,10,15} and cholesky dw bits
    indices_cgd = [4, 9, 14, 19]
    mean_size_cholesky = np.nanmean(data[:,:,:,0,5], axis=(0, 2))
    mean_size_cgd = np.nanmean(data2[:,:,:,:,3], axis=(0, 2))
    mean_error_cgd = np.nanmean(data2[:,:,:,:,0], axis=(0, 2))
    mean_error_cholesky = np.nanmean(data[:,:,:,0,4], axis=(0, 2))
    std_error_cholesky = np.nanstd(data[:,:,:,0,4], axis=(0, 2))

    # compute confidence intervals
    cis_error_cgd = np.ndarray(shape=(len(ds), num_iterations, 2))
    cis_error_cholesky = np.ndarray(shape=(len(ds), 2))
    for i_d in xrange(len(ds)):
        for iteration in xrange(num_iterations):
            data_flat = data2[:, i_d, :, iteration, 0].flat
            cis_error_cgd[i_d, iteration] = scikits.bootstrap.ci(data_flat, method="abc")
        data_flat=data[:, i_d, :, 0, 4].flat
        cis_error_cholesky[i_d] = scikits.bootstrap.ci(data_flat, method="abc")

    colours = ['#404096', '#529DB7', '#7DB874', '#E39C37', '#D92120', '#000000']
    colourcycler = cycle(colours)

    plt.xscale('log')
    plt.xlabel('$d$')
    plt.xticks(ds, ["${}$".format(d) for d in ds]) # axes in mathmode
    plt.yscale('log')
    plt.ylabel('Error')
    plt.xlim(10,501)

    yerr = [mean_error_cholesky - cis_error_cholesky[:,0], cis_error_cholesky[:,1] - mean_error_cholesky]
    plt.errorbar(ds, mean_error_cholesky, marker='.', c=next(colourcycler), yerr=yerr)
    for i in indices_cgd:
        yerr = [mean_error_cgd[:,i] - cis_error_cgd[:,i,0], cis_error_cgd[:,i,1] - mean_error_cgd[:,i]]
        plt.errorbar(ds, mean_error_cgd[:,i], marker='.', c=next(colourcycler), yerr=yerr)
    plt.legend(["\small Cholesky"] + ["\small CGD {}".format(index + 1) for index in indices_cgd], loc=3, ncol=3, mode="expand")
    plt.tight_layout()
    plt.gca().set_ylim(bottom=(1e-8 if bw == 32 else 1e-16))
    plt.savefig("plot_phase2_accuracy_vs_d_bw{}.pdf".format(bw), transparent=True)
    plt.show()

    print "Average condition number: {}".format(np.mean(data[:,:,:,:,0]))
