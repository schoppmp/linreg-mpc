import os
import argparse
from generate_tests import (generate_lin_regression, write_lr_instance)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generates vertically partitioned linear regressison datasets')
    parser.add_argument('n', help='Number of records', type=int)
    parser.add_argument('d', help='Number of features', type=int)
    parser.add_argument('p', help='Number of parties', type=int)
    parser.add_argument('dest_folder', help='Destination folder')
    parser.add_argument(
        'num_examples', help='Number of examples to be generated', type=int)
    parser.add_argument(
        '--verbose', '-v', action='store_true', help='Run in verbose mode')

    args = parser.parse_args()
    VERBOSE = args.verbose
    assert args.p <= args.d

    # This corresponds to an experiment setup as in Nikolaenloks S&P paper:
    # "Privacy-Preserving Ridge Regression on Hundreds of Millions of Records"
    for i in range(args.num_examples):
        filename_lr = 'test_LR_{0}x{1}_{2}_{3}.test'.format(
            args.n, args.d, args.p, i)
        filepath_lr = os.path.join(args.dest_folder, filename_lr)
        (X, y, beta, e) = generate_lin_regression(args.n, args.d)
        write_lr_instance(X, y, beta, filepath_lr, args.p)
        if VERBOSE:
            print('Wrote instance in file {0}'.format(filepath_lr))
