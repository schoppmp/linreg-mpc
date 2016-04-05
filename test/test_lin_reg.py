VERBOSE = False

from scipy import random, linalg, spatial
from generate_tests import generate_lin_system
import argparse
import numpy
import os
import subprocess
import re

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Tests our linear regression implementations. '
        'Only testing PD linear system solving at the moment')
    parser.add_argument('exec_path', help='Path to our executable.')
    parser.add_argument('algorithm', help='Must be cgd, cholesky or ldlt.')
    parser.add_argument('n', help='Number of rows', type=int)
    parser.add_argument('d', help='Number of columns', type=int)
    parser.add_argument('num_iters_cgd', help='Number of iterations for cgd', type=int)
    parser.add_argument('dest_folder', help='Destination folder for the results')
    parser.add_argument('num_examples', help='Number of instances to be ran',
        type=int)
    parser.add_argument('--verbose', '-v', action='store_true',
        help='Run in verbose mode')
    args = parser.parse_args()
    assert args.algorithm in ['cgd', 'cholesky', 'ldlt']
    VERBOSE = args.verbose
    for i in range(args.num_examples):
        filename_ls = 'test_LS_{0}x{1}_{2}.test'.format(args.n, args.d, i)
        filename_ls_out = 'test_LS_{0}x{1}_{2}.test.out'.format(
            args.n, args.d, i)
        filepath_ls = os.path.join(args.dest_folder, filename_ls)
        filepath_ls_out = os.path.join(args.dest_folder, filename_ls_out)
        (A, mask_A, b, mask_b, solution) = generate_lin_system(
            args.n, args.d, filepath_ls)
        if VERBOSE:
            print 'Generated example {0}'.format(filename_ls)
            print 'Solving {0} with {1}'.format(filename_ls, args.algorithm)
        cmd = [args.exec_path, '1234', None, filepath_ls,
            args.algorithm, str(args.num_iters_cgd)]
        cmd1 = cmd[:2] + ['1'] + cmd[3:]
        cmd2 = cmd[:2] + ['2'] + cmd[3:]
        subprocess.Popen(cmd1)
        s = subprocess.check_output(cmd2)
        print s
        lines = s.split('\n')
        for line in lines:
            m = re.match('Algorithm:\s*(\S+)', line)
            if m:
                alg = m.group(1)
            m = re.match('Time\s+elapsed:\s*(\S+)', line)
            if m:
                time = float(m.group(1))
            m = re.match('Number\s+of\s+gates:\s*(\S+)', line)
            if m:
                gate_num = int(m.group(1))
            m = re.match('Result:\s*(.+)', line)
            if m:
                result = map(float, m.group(1).split())

                #print result
                print 'solution: ', solution
                print 'error: ', spatial.distance.euclidean(result, solution)
