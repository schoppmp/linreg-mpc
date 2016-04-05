VERBOSE = False
from scipy import random, linalg
import argparse
import numpy
import os
import sys


def write_system(A, b, solution, filepath):
    assert numpy.allclose(A.dot(solution), b)
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
        f.write('\n')
        f.write('{0}\n'.format(solution.shape[0]))
        for i in range(solution.shape[0]):
            f.write(str(solution[i]))
            f.write(' ')


def write_sls_instance(A, A_, b, b_, solution, filepath):
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
            f.write(' ')
        f.write('\n')
        f.write('{0} {1}\n'.format(A.shape[0], A.shape[1]))
        for i in range(A_.shape[0]):
            for j in range(A_.shape[1]):
                f.write(str(A_[i][j]))
                f.write(' ')
            f.write('\n')
        f.write('{0}\n'.format(b_.shape[0]))
        for i in range(b_.shape[0]):
            f.write(str(b_[i]))
            f.write(' ')
        f.write('\n')
        f.write('{0}\n'.format(solution.shape[0]))
        for i in range(solution.shape[0]):
            f.write(str(solution[i]))
            f.write(' ')


def generate_sls_instance_from_regression_problem(n, d, lambda_, filepath):
    if not lambda_:
        (A, b, solution) = generate_lin_system_from_regression_problem(
            n, d, float(d)/n)
    else:
        (A, b, solution) = generate_lin_system_from_regression_problem(
            n, d, lambda_)
    mask_A = random.uniform(low=-1, high=1, size=(d, d))
    mask_b = random.uniform(low=-1, high=1, size=d)
    # masked_A = A + mask_A
    # masked_b = b + mask_b
    if filepath:
        write_sls_instance(A, mask_A, b, mask_b, solution, filepath)
    # A_test = masked_A - mask_A
    # b_test = masked_b - mask_b
    assert numpy.allclose(A.dot(solution), b)

    return (A, mask_A, b, mask_b, solution)


def generate_lin_system(n, d, filepath=None):
    X = random.randn(n, d)
    A = 1./n*X.T.dot(X)
    y = random.uniform(low=-1, high=1, size=d)
    b = A.dot(y)
    # -10 and 10 are an arbitrary choice here
    mask_A = random.uniform(low=-10, high=10, size=(d, d))
    mask_b = random.uniform(low=-10, high=10, size=d)
    if filepath:
        # write_system(A, b, y, filepath)
        write_sls_instance(A, mask_A, b, mask_b, y, filepath)
    return (A, mask_A, b, mask_b, y)


def generate_lin_system_from_regression_problem(n, d, lambda_, filepath=None):
    (X, y, beta, e) = generate_lin_regression(n, d)
    A = 1./n*X.T.dot(X) + numpy.inner(numpy.identity(d), lambda_)
    b = 1./n*X.T.dot(y)
    x = linalg.solve(A, b)
    if filepath:
        write_system(A, b, x)
    return (A, b, x)


def generate_lin_regression(n, d, filepath=None):
    X = random.uniform(low=-1, high=1, size=(n, d))
    beta = random.uniform(low=-1, high=1, size=d)
    mu, sigma = 0, 1  # mean and standard deviation
    e = numpy.array(random.normal(mu, sigma, n))
    y = X.dot(beta) + e.T
    return (X, y, beta, e)


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

    sys.exit()
    # This corresponds to an experiment setup as in Nikolaenloks S&P paper:
    # "Privacy-Preserving Ridge Regression on Hundreds of Millions of Records"
    for i in range(args.num_matrices):
        filename_lr = 'test_LR_{0}x{1}_{2}.test'.format(args.n, args.d, i)
        filename_ls = 'test_LS_{0}x{1}_{2}.test'.format(args.n, args.d, i)
        filepath_lr = os.path.join(args.dest_folder, filename_lr)
        filepath_ls = os.path.join(args.dest_folder, filename_ls)
        (A, mask_A, b, mask_b, solution) = generate_sls_instance_from_regression_problem(
            args.n, args.d, None, filepath_ls)
