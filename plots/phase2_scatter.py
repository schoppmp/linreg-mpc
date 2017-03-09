from matplotlib import rc, pyplot as plt
import numpy as np
import glob
import os
from itertools import cycle
import random

for bw in [32, 64]:
    if bw == 64:
        dirname = "experiments/results/phase2_accuracy_64_100/"
    else:
        dirname = "experiments/results/phase2_accuracy_32_100/"

    files_cgd = glob.glob(os.path.join(dirname, "*_cgd_*.out"))
    # if bw == 32: # only take half of the files
    #     files_cgd = [files_cgd[i] for i in random.sample(xrange(len(files_cgd)), 100)]
    num_iterations = 20
    # file x iteration -> (error_dist, error_objective)
    data_cgd = np.ndarray(shape=(len(files_cgd), num_iterations, 2))
    data_cgd[:] = np.NAN
    # file -> condition number
    condition_numbers_cgd = np.ndarray(shape=(len(files_cgd)))
    condition_numbers_cgd[:] = np.NAN
    for i_f, filename in enumerate(files_cgd):
        lines = open(filename).read().splitlines()
        index_obj = lines.index("Objective function on solution:") + 1
        objective_on_solution = lines[index_obj]
        condition_numbers_cgd[i_f] = lines[-1]
        for iteration in xrange(num_iterations):
            # This is to ignore files with wrong format
            try:
                error_dist, objective = lines[3+iteration].split()[1:3]
                error_objective = abs(float(objective) - float(objective_on_solution)) / float(objective_on_solution)
                data_cgd[i_f, iteration, 0:2] = error_dist, error_objective
            except Exception as e:
                print filename

    files_cholesky = glob.glob(os.path.join(dirname, "*_cholesky_*.out"))
    # file x iteration -> (error_dist, error_objective)
    data_cholesky = np.ndarray(shape=(len(files_cholesky)))
    data_cholesky[:] = np.NAN
    # file -> condition number
    condition_numbers_cholesky = np.ndarray(shape=(len(files_cholesky)))
    condition_numbers_cholesky[:] = np.NAN
    for i_f, filename in enumerate(files_cholesky):
        lines = open(filename).read().splitlines()
        index_obj = lines.index("Objective function on solution:") + 1
        objective_on_solution = lines[index_obj]
        condition_numbers_cholesky[i_f] = lines[-1]
        index_result = lines.index("result:") + 2
        result = np.array(map(float, lines[index_result].split()))
        error_dist = lines[1].split()[5]
        objective = None  # We do not have the objective value on Cholesky instances
        #error_objective = abs(float(objective) - float(objective_on_solution))
        data_cholesky[i_f] = error_dist


    # set pyplot look
    rc('text', usetex=True)
    rc('text.latex', preamble='\usepackage{lmodern}')
    rc('lines', linewidth=1)
    rc('patch', linewidth=1)
    rc('axes', linewidth=1)
    rc('figure', figsize=(4.5, 3))
    #rc('errorbar', capsize=5)
    rc('savefig', format='pdf')

    ax = plt.gca()
    symbols = ["s", "*", "d", "v", "."]

    colours = ['#404096', '#529DB7', '#7DB874', '#E39C37', '#D92120', '#000000']
    #colours = ['#57a3ad', '#dea73a', '#d92120']
    colourcycler = cycle(colours)
    symbolcycler = cycle(symbols)
    #next(colourcycler)
    #next(symbolcycler)
    iters=[4,9,14,19]
    ax.scatter(condition_numbers_cholesky, data_cholesky, c=next(colourcycler), marker=next(symbolcycler), linewidth=0.1)
    for iteration in iters:
       ax.scatter(condition_numbers_cgd, data_cgd[:,iteration,0], c=next(colourcycler), marker=next(symbolcycler), linewidth=0.1)
    ax.set_yscale('log')
    #ax.set_xscale('log')
    #ax.set_xlim([1,11])
    if bw == 64:
        ax.set_ylim([1e-18, 1])
    else:
        ax.set_ylim([1e-6, 100])
    plt.legend(["\small Cholesky"] + ["\small CGD {}".format(i+1) for i in iters], loc=3, ncol=3, mode="expand")
    #plt.legend(["CGD {}".format(i+1) for i in iters], loc=4)
    plt.ylabel(r"Error")
    plt.xlabel(r"Condition Number $\kappa$")
    plt.tight_layout()
    plt.savefig("plot_scatter_2_norm_{}.pdf".format(bw), transparent=True)
    plt.show()
