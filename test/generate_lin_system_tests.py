from generate_tests import (generate_lin_system)
import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='A generator for pseudorandom positive definitive matrices')
    parser.add_argument('n', help='Number of rows', type=int)
    parser.add_argument('d', help='Number of columns', type=int)
    parser.add_argument('dest_folder', help='Destination folder')
    parser.add_argument('num_matrices', help='Number of matrices to be generated', type=int)
    parser.add_argument('--verbose', '-v', action='store_true', help='Run in verbose mode')
    
    args = parser.parse_args()
    VERBOSE = args.verbose

    # This corresponds to the experiments setup in
    # https://adriaborja.slack.com/files/borja/F0XHUTYUA/Experimental_Setup___Plots
    for i in range(args.num_matrices):
        filename_ls = 'test_LS_{0}x{1}_{2}.test'.format(args.n, args.d, i)
        filepath_ls = os.path.join(args.dest_folder, filename_ls)
        A, mask_A, b, mask_b, solution = generate_lin_system(
            args.n, args.d, filepath_ls)
        if VERBOSE:
            print('Wrote linear system in file {0}'.format(filepath_ls))
