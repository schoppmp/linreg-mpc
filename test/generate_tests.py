VERBOSE = False
from scipy import random, linalg
import argparse
import numpy
import os

def generate_lin_system(n, d, lambda_, filepath=None):
    (X, y, beta, e) = generate_lin_regression(n, d)
    A = X.T.dot(X) + numpy.inner(numpy.identity(d), lambda_)
    b = X.T.dot(y)
    if filepath:
        with open(filepath, 'w') as f:
            f.write('{0} {1}\n'.format(A.shape[0], A.shape[1]))
            for i in range(A.shape[0]):
                for j in range(A.shape[1]):
                    f.write(str(A[i][j]))
                    f.write(' ')
                f.write('\n')
            f.write('{0}\n'.format(b.shape[0]))
            for i in range(b.shape[0]):
                f.write(str(b[i]))
    return (A, b)

def generate_lin_regression(n, d, filepath=None):
    assert d>1
    X = random.rand(n, d)
    beta = random.rand(d)
    mu, sigma = 0, 0.1 # mean and standard deviation
    e = numpy.array(random.normal(mu, sigma, n))
    y = X.dot(beta) + e.T
    return (X, y, beta, e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A generator for pseudorandom positive definitive matrices')
    parser.add_argument('n', help='Number of rows', type=int)
    parser.add_argument('d', help='Number of columns', type=int)
    parser.add_argument('dest_folder', help='Destination folder')
    parser.add_argument('num_matrices', help='Number of matrices to be generated', type=int)
    parser.add_argument('--verbose', '-v', action='store_true', help='Run in verbose mode')
    
    args = parser.parse_args()
    VERBOSE = args.verbose
    
    for i in range(args.num_matrices):
        filename_lr = 'test_LR_{0}{1}_{2}.test'.format(args.n, args.d, i)
        filename_ls = 'test_LS_{0}{1}_{2}.test'.format(args.n, args.d, i)
        filepath_lr = os.path.join(args.dest_folder, filename_lr)
        filepath_ls = os.path.join(args.dest_folder, filename_ls)
        #generate_lin_regression(args.n, args.d, filepath_lr)
        (A, b) = generate_lin_system(args.n, args.d, 3, filepath_ls)

