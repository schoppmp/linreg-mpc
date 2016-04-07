VERBOSE = False

from scipy import random, linalg, spatial
from generate_tests import generate_lin_system
import argparse
import numpy
import os
import subprocess
import re


def parse_output(n, d, alg, solution, s, filepath_ls_out):
    print s
    f = open(filepath_ls_out, 'w')
    cgd_iter_solutions = []
    cgd_iter_gate_sizes = []
    lines = s.split('\n')
    for line in lines:
        if alg == 'cgd':
            m = re.match('m\s+=\s+((\s*[\d\.-]+)+)', line)
            if m:
                scaling = map(float, m.group(1).split())
            m = re.match('((\s*[\d\.-]+)+)', line)
            if m:
                scaled_solution = map(float, m.group(1).split())
                rescaled_solution = [
                    scaled_solution[i]/scaling[i]
                    for i in range(len(scaling))]
                cgd_iter_solutions.append(rescaled_solution)
            m = re.match('\s*Yao\'s\s+gates\s+count:\s+(.+)$', line)
            if m:
                cgd_iter_gate_sizes.append(int(m.group(1)))
        m = re.match('Algorithm:\s*(\S+)', line)
        if m:
            pass#assert alg == m.group(1)
        m = re.match('Time\s+elapsed:\s*(\S+)', line)
        if m:
            time = float(m.group(1))
        m = re.match('Number\s+of\s+gates:\s*(\S+)', line)
        if m:
            gate_count = int(m.group(1))
        m = re.match('Result:\s*(.+)', line)
        if m:
        #print solution
        #print cgd_iter_solutions
            result = map(float, m.group(1).split())
            error = spatial.distance.euclidean(result, solution)
            f.write('n d algorithm time error gate_count')
            f.write('\n{0} {1} {2} {3} {4} {5}'.format(n, d,
                alg, time, error, gate_count))
            if alg == 'cgd':
                gate_count_after_iters =\
                    gate_count - cgd_iter_gate_sizes[-1]
                cgd_iter_gate_sizes = map(
                    lambda x: x+gate_count_after_iters,
                    cgd_iter_gate_sizes)
                assert len(cgd_iter_gate_sizes) == len(cgd_iter_solutions),\
                    '{0}\n{1}\n{2}\n{3}'.format(
                        len(cgd_iter_solutions),
                        cgd_iter_solutions,
                        len(cgd_iter_gate_sizes),
                        cgd_iter_gate_sizes)
                f.write('\niter_i error_i gate_count_i')
                for i in range(len(cgd_iter_solutions)):
                    error_i = spatial.distance.euclidean(
                        cgd_iter_solutions[i], solution)
                    f.write('\n{0} {1} {2}'.format(
                        i+1, error_i, cgd_iter_gate_sizes[i]))
    f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Tests our linear regression implementations. '
        'Only testing PD linear system solving at the moment')
    parser.add_argument('exec_path', help='Path to our executable.')
    parser.add_argument('algorithm', help='Must be cgd, cholesky, ldlt, or all.')
    parser.add_argument('n', help='Number of rows', type=int)
    parser.add_argument('d', help='Number of columns', type=int)
    parser.add_argument('num_iters_cgd', help='Number of iterations for cgd', type=int)
    parser.add_argument('dest_folder', help='Destination folder for the results')
    parser.add_argument('num_examples', help='Number of instances to be ran',
        type=int)
    parser.add_argument('--verbose', '-v', action='store_true',
        help='Run in verbose mode')
    args = parser.parse_args()
    assert args.algorithm in ['cgd', 'cholesky', 'ldlt', 'all']
    if args.algorithm == 'all':
        algorithms = ['cgd', 'cholesky', 'ldlt']
    else:
        algorithms = [args.algorithm]
    VERBOSE = args.verbose
    for example in range(args.num_examples):
        filename_ls = 'test_LS_{0}x{1}_{2}.test'.format(
            args.n, args.d, example)
        filepath_ls = os.path.join(args.dest_folder, filename_ls)
        (A, mask_A, b, mask_b, solution) = generate_lin_system(
            args.n, args.d, filepath_ls)
        if VERBOSE:
            print 'Generated example {0}'.format(filename_ls)
        for alg in algorithms:
            filename_ls_out = 'test_LS_{0}x{1}_{2}_{3}.test.out'.format(
                args.n, args.d, alg, example)
            filepath_ls_out = os.path.join(args.dest_folder, filename_ls_out)
            if VERBOSE:
                print 'Solving {0} with {1}'.format(filename_ls, alg)
            cmd = [args.exec_path, '1234', None, filepath_ls,
                alg, str(args.num_iters_cgd)]
            cmd1 = cmd[:2] + ['1'] + cmd[3:]
            cmd2 = cmd[:2] + ['2'] + cmd[3:]
            subprocess.Popen(cmd1)
            s = subprocess.check_output(cmd2)
            parse_output(args.n, args.d, alg, solution, s, filepath_ls_out)
