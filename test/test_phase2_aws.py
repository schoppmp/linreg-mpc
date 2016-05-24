import os
import argparse
from generate_tests import (generate_lin_system_from_regression_problem, generate_lin_system)
import paramiko
import numpy
import re
from scipy import random, linalg, spatial

REMOTE_USER = 'ubuntu'
#KEY_FILE = '/home/ubuntu/.ssh/id_rsa'
KEY_FILE = '/home/agascon/Desktop/experiments1.pem'

def parse_output(n, d, alg, solution, filepath_ls_out, filepath_ls_exec):
    with open(filepath_ls_exec, 'r') as f_exec:
        lines = f_exec.readlines()
    f = open(filepath_ls_out, 'w')
    cgd_iter_solutions = []
    cgd_iter_gate_sizes = []
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
            print error, alg, filepath_ls_exec
            if alg == 'cgd':
                #print cgd_iter_gate_sizes, filepath_ls_out
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
    parser = argparse.ArgumentParser(description='Runs phase 2 experiments')
    parser.add_argument('exec_file', help='Executable')
    parser.add_argument('dest_folder', help='Destination folder')
    parser.add_argument(
        'num_examples', help='Number of executions of every setting', type=int)
    parser.add_argument(
        '--verbose', '-v', action='store_true', help='Run in verbose mode')
    parser.add_argument(
        '--process', help='Only process data in folder', required=False)


    args = parser.parse_args()
    VERBOSE = args.verbose
    #assert args.p <= args.d

    if args.process:
        testcases = []
        for f in os.listdir(args.process):
            print args.process
            if f.endswith(".exec"):
                print f
                ##print i
                m = re.match('test_LS_([0-9]+)x([0-9]+)_([0-9]\.[0-9])_([0-9])_(\S+)_([0-9]+)_p([1-2]).exec', f)
                assert m, f
                n = int(m.group(1))
                d = int(m.group(2))
                sigma = float(m.group(3))
                exec_num = int(m.group(4))
                alg = m.group(5)
                iters = int(m.group(6))
                num_party = int(m.group(7))
                testcases.append((n, d, sigma, exec_num, alg, iters, num_party))
            else:
                continue
        for tc in sorted(testcases):
            #print tc
            n, d, sigma, exec_num, alg, iters, num_party = tc[0], tc[1], tc[2], tc[3], tc[4], tc[5], tc[6]
            if d >= 500: continue
            file_exec = 'test_LS_{0}x{1}_{2}_{3}_{4}_{5}_p{6}.exec'.format(
                n, d, sigma, exec_num, alg, iters, num_party)
            file_out = 'test_LS_{0}x{1}_{2}_{3}_{4}_{5}.out'.format(
                n, d, sigma, exec_num, alg, iters, num_party)
            file_in = 'test_LS_{0}x{1}_{2}_{3}.in'.format(n, d, sigma, exec_num)
            with open(file_in, 'r') as fd:
                lines = fd.readlines()
                solution = map(lambda x : float(x), lines[-1].split())
                #print solution
                #print lines

                parse_output(n, d, alg, solution, file_out, file_exec)
        sys.exit()

    ips_file = 'aws_ips_phase2'
    if True:#args.ips_file:
        public_ips = []
        private_ips = []
        with open(ips_file, 'r') as f:
            for i, line in enumerate(f.readlines()):
                public_ips.append(line.split()[0])
                private_ips.append(line.split()[1])
    else:
        public_ips = None
        private_ips = None

    def update_and_compile(ip):
        key = paramiko.RSAKey.from_private_key_file(KEY_FILE)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=ip, username=REMOTE_USER, pkey=key)
        cmd_cd = 'cd secure-distributed-linear-regression; pwd; git stash; git checkout master; git pull; make clean; make OBLIVCC=~/obliv-c/bin/oblivcc ; killall -9 test_linear_system'
        stdin, stdout, stderr = client.exec_command(cmd_cd)
        for line in stdout:
            print '... ' + line.strip('\n')
        for line in stderr:
            print '... ' + line.strip('\n')

        client.close()

    if public_ips:
        for ip in public_ips:
            update_and_compile(ip)

    def run_remotely(dest_folder, input_filepath, input_filename, ip, exec_cmd):
        key = paramiko.RSAKey.from_private_key_file(KEY_FILE)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=ip, username=REMOTE_USER, pkey=key)
        sftp = client.open_sftp()
        try:
            sftp.chdir(dest_folder)  # Test if remote_path exists
        except IOError:
            sftp.mkdir(dest_folder)  # Create remote_path
            sftp.chdir(dest_folder)
        sftp.put(input_filepath, input_filename)
        print ip, cmd
        stdin, stdout, stderr = client.exec_command(cmd)
        for line in stdout:
            print '... ' + line.strip('\n')
        for line in stderr:
            print '... ' + line.strip('\n')
        #sftp.remove(input_filename)
        client.close()

    alg = 'cholesky'
    num_iters_cgd = 15

    #for alg in ['cgd', 'cholesky', 'ldlt']:
    for i in range(args.num_examples):
        for alg in ['cgd', 'cholesky']:
            for sigma in [0.1]:
                for d in [10, 20, 50, 100]:
                    for n in [d, 2*d, 5*d, 10*d, 1000*d]:
                        print n, d, sigma, alg, num_iters_cgd
                        filename_ls_in = 'test_LS_{0}x{1}_{2}_{3}_nik.in'.format(n, d, sigma, i)
                        filepath_ls_in = os.path.join(args.dest_folder, filename_ls_in)

                        #(X, y, beta) = generate_lin_system_from_regression_problem(
                        #    n, d, sigma, filepath_ls_in)
                        (X, y, beta) = generate_lin_system(n, d, filepath_ls_in) 

                        if VERBOSE:
                            print('Wrote instance in file {0}'.format(filepath_ls_in))

                        for party in [1, 2]:
                            filename_ls_exec = 'test_LS_{0}x{1}_{2}_{3}_nik_{4}_{5}_p{6}.exec'.format(n, d, sigma, i, alg, num_iters_cgd, party)
                            filepath_ls_exec = os.path.join(
                                args.dest_folder, filename_ls_exec)
                            filename_ls_out = os.path.splitext(filename_ls_exec)[0] + '.out'

                            cmd = '{0} 1234 {1} {2} {3} {4} > {5} {6}'.format(
                                args.exec_file,
                                party,
                                filepath_ls_in,
                                alg,
                                num_iters_cgd,
                                filepath_ls_exec,
                                '&' if party == 1 else '')

                            #run_remotely(args.dest_folder, filepath_ls_in,
                            #    filename_ls_in, public_ips[party-1], cmd)

                            # To run both parties in the same machine
                            run_remotely(args.dest_folder, filepath_ls_in,
                                filename_ls_in, public_ips[0], cmd)
