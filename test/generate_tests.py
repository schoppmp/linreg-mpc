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
            f.write(' ')
        f.write('\n')
        f.write('{0}\n'.format(solution.shape[0]))
        for i in range(solution.shape[0]):
            f.write(str(solution[i]))
            f.write(' ')


def write_lr_instance(X, y, solution, filepath, num_parties=1, endpoints=None):
    """
    Generates an instance of a vertucally partitioned Linear Regression
    problem ans writes it in [filepath]
    """
    n = X.shape[0]
    d = X.shape[1]
    assert y.shape[0] == n, y.shape[0]
    assert solution.shape[0] == d
    assert num_parties > 0
    if endpoints:
        assert len(endpoints) >= num_parties
    with open(filepath, 'w') as f:
        #f.write('// n d num_parties\n')
        f.write('{0} {1} {2}\n'.format(n, d, num_parties))
        #f.write('// TI's endpoint\n')
        if not endpoints:
            f.write('localhost:{0}\n'.format(1234))
        else:
            f.write('{0}\n'.format(endpoints[0]))
        if num_parties > 1:
            # We assume an even partition of (A,b) among the parties
            # Last party gets num_features mod num_parties additional features
            i = 0
            #f.write('// endpoint and initial index of features from each party\n')
            for p in range(num_parties):
                if not endpoints:
                    f.write('localhost:{0} {1}\n'.format(1234 + p + 1, i))
                else:
                    f.write('{0} {1}\n'.format(endpoints[p + 1], i))
                i += d / num_parties
        #f.write('// X:\n')
        f.write('{0} {1}\n'.format(n, d))
        for i in range(n):
            for j in range(d):
                f.write(str(X[i][j]))
                f.write(' ')
            f.write('\n')
        #f.write('// y (owned by last party):\n')
        f.write('{0}\n'.format(n))
        for i in range(n):
            f.write(str(y[i]))
            f.write(' ')
        f.write('\n')
        #f.write('// beta (solution):\n')
        f.write('{0}\n'.format(d))
        for i in range(d):
            f.write(str(solution[i]))
            f.write(' ')
        f.write('\n')
        #f.write('// XX^T:\n')
        cov = 1./(d*n)*X.T.dot(X)
	b = 1./(d*n)*X.T.dot(y)
	assert b.shape[0] == d
        assert cov.shape[0] == d
        assert cov.shape[1] == d
        f.write('{0} {0}\n'.format(d))
        for i in range(d):
            for j in range(d):
                f.write(str(cov[i][j]))
                f.write(' ')
            f.write('\n')
	f.write('{0}\n'.format(d))
	for i in range(d):
		f.write(str(b[i]))
		f.write(' ')


def generate_sls_instance_from_regression_problem(
        n, d, lambda_, filepath, num_parties=1):
    if not lambda_:
        (A, b, solution) = generate_lin_system_from_regression_problem(
            n, d, float(d) / n)
    else:
        (A, b, solution) = generate_lin_system_from_regression_problem(
            n, d, lambda_)
    if filepath:
        write_sls_instance(A, b, solution, filepath, num_parties)
    assert numpy.allclose(A.dot(solution), b)
    return (A, b, solution)


def generate_lin_system(n, d, filepath=None):
    X = random.randn(n, d)
    A = 1. / n * X.T.dot(X)
    y = random.uniform(low=-1, high=1, size=d)
    b = A.dot(y)
    # -10 and 10 are an arbitrary choice here
    mask_A = random.uniform(low=-10, high=10, size=(d, d))
    mask_b = random.uniform(low=-10, high=10, size=d)
    if filepath:
        write_system(A, b, y, filepath)
    return (A, mask_A, b, mask_b, y)


def generate_lin_system_from_regression_problem(n, d, lambda_, filepath=None):
    (X, y, beta, e) = generate_lin_regression(n, d)
    A = 1. / n * X.T.dot(X) + numpy.inner(numpy.identity(d), lambda_)
    b = 1. / n * X.T.dot(y)
    x = linalg.solve(A, b)
    if filepath:
        write_system(A, b, x)
    return (A, b, x)


def generate_lin_regression(n, d, filepath=None, parties=1):
    """
    Generates a synthetic linear regression instance as in
    "Privacy-Preserving Ridge Regression on Hundreds of Millions of Records"
    """
    X = random.uniform(low=-1, high=1, size=(n, d))
    beta = random.uniform(low=-1, high=1, size=d)
    mu, sigma = 0, 1  # mean and standard deviation
    e = numpy.array(random.normal(mu, sigma, n))
    y = X.dot(beta) + e.T
    return (X, y, beta, e)
