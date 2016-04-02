VERBOSE = False

from generate_tests import generate_sls_instance
from scipy import random, linalg
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
    parser.add_argument('dest_folder', help='Destination folder for the results')
    parser.add_argument('num_examples', help='Number of instances to be ran',
        type=int)
    parser.add_argument('--verbose', '-v', action='store_true',
        help='Run in verbose mode')
    args = parser.parse_args()
    assert args.algorithm in ['cgd', 'cholesky', 'ldlt']
    VERBOSE = args.verbose
    for i in range(args.num_examples):
        # filename_lr = 'test_LR_{0}x{1}_{2}.test'.format(args.n, args.d, i)
        filename_ls = 'test_LS_{0}x{1}_{2}.test'.format(args.n, args.d, i)
        filename_ls_out = 'test_LS_{0}x{1}_{2}.test.out'.format(
            args.n, args.d, i)
        # filepath_lr = os.path.join(args.dest_folder, filename_lr)
        filepath_ls = os.path.join(args.dest_folder, filename_ls)
        filepath_ls_out = os.path.join(args.dest_folder, filename_ls_out)
        (A, mask_A, b, mask_b, solution) = generate_sls_instance(
            args.n, args.d, None, filepath_ls)
        if VERBOSE:
            print 'Generated example {0}'.format(filename_ls)
            print 'Solving {0} with {1}'.format(filename_ls, args.algorithm)
        cmd1 = '{0} 1234 1 {1}'.format(args.exec_path, filepath_ls)
        subprocess.Popen(cmd1.split())
        cmd2 = '{0} 1234 2 {1}'.format(args.exec_path, filepath_ls)
        s = subprocess.check_output(cmd2.split())
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
        	m = re.match('Result:\s*( +)', line)
        	if m:
        		result = map(float, m.group(1).split())

       	print result
       	print solution


