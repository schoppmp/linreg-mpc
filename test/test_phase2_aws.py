import os
import argparse
from generate_tests import (generate_lin_system_from_regression_problem, generate_lin_system)
import paramiko
import re
import time
import logging

REMOTE_USER = 'ubuntu'
KEY_FILE = '/home/ubuntu/.ssh/id_rsa'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def update_and_compile(ip, remote_ip):
    key = paramiko.RSAKey.from_private_key_file(KEY_FILE)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=ip, username=REMOTE_USER, pkey=key)

    cmd = 'cd secure-distributed-linear-regression; '
    'pwd; git stash; git checkout experiments_phase_1; '
    'git pull; make clean; make REMOTE_HOST={0}; '.format(remote_ip)
    'killall -9 test_linear_system'
    logger.info('Sending compilation command to {0}:'.format(ip))
    logger.info('{0}'.format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    for line in stdout:
        logger.info('... ' + line.strip('\n'))
    for line in stderr:
        logger.error('... ' + line.strip('\n'))

    client.close()


def parse_output(n, d, alg, solution, filepath_ls_out, filepath_ls_exec,
        alg_has_scaling=False):
    """
    Generates a .out file containing accuracy information given
    an .exec file with execution information
    (e.g. intermediate solutions of cgd) for a specific test case.
    """
    with open(filepath_ls_exec, 'r') as f_exec:
        lines = f_exec.readlines()
    cgd_iter_solutions = []
    cgd_iter_gate_sizes = []
    for line in lines:
        """
        The following code relies on the format of the implementation's
        output format for algorithms cgd, cholesky, and ldlt.
        For the version of cgd that has scaling, [alg_has_scaling]
        should be set to true, otherwise intermediate accuracy values
        will not be correct
        """
        if alg == 'cgd':
            if alg_has_scaling:
                # Reading scaling value m
                m = re.match('m\s+=\s+((\s*[\d\.-]+)+)', line)
                if m:
                    scaling = map(float, m.group(1).split())
                # Reading intermediate solution for cgd with scaling
                m = re.match('((\s*[\d\.-]+)+)', line)
                if m:
                    scaled_solution = map(float, m.group(1).split())
                    rescaled_solution = [
                        scaled_solution[i] / scaling[i]
                        for i in range(len(scaling))]
                    cgd_iter_solutions.append(rescaled_solution)
            else:
                # Reading intermediate solution for cgd without scaling
                m = re.match('((\s*[\d\.-]+)+)', line)
                if m:
                    partial_solution = map(float, m.group(1).split())
                    cgd_iter_solutions.append(partial_solution)
            # Reading intermediate gate count for cgd
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
            result = map(float, m.group(1).split())
            # At this point we have all the data we need to produce the
            # .out file
            f = open(filepath_ls_out, 'w')
            error = spatial.distance.euclidean(result, solution)
            f.write('n d algorithm time error gate_count')
            f.write('\n{0} {1} {2} {3} {4} {5}'.format(n, d,
                alg, time, error, gate_count))
            if alg == 'cgd':
                gate_count_after_iters =\
                    gate_count - cgd_iter_gate_sizes[-1]
                cgd_iter_gate_sizes = map(
                    lambda x: x + gate_count_after_iters,
                    cgd_iter_gate_sizes)
                assert len(cgd_iter_gate_sizes) == len(
                    cgd_iter_solutions), '{0}\n{1}\n{2}\n{3}'.format(
                        len(cgd_iter_solutions),
                        cgd_iter_solutions,
                        len(cgd_iter_gate_sizes),
                        cgd_iter_gate_sizes)
                f.write('\niter_i error_i gate_count_i')
                for i in range(len(cgd_iter_solutions)):
                    error_i = spatial.distance.euclidean(
                        cgd_iter_solutions[i], solution)
                    f.write('\n{0} {1} {2}'.format(
                        i + 1, error_i, cgd_iter_gate_sizes[i]))
    f.close()


def run_instance_remotely(n, d, alg, solution,
        remote_working_dir,
        remote_dest_folder, local_dest_folder,
        local_input_filepath, remote_exec_filepath,
        ip, exec_cmd, is_party_2):
    """
        Executes an instance of phase 2 on a remote machine, collecting the
        result (if party two was executed), and parsing it to produce the
        corresponding .out file in [local_dest_folder]
    """
    key = paramiko.RSAKey.from_private_key_file(KEY_FILE)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=ip, username=REMOTE_USER, pkey=key)
    sftp = client.open_sftp()
    try:
        sftp.chdir(remote_dest_folder)  # Test if remote_path exists
    except IOError:
        sftp.mkdir(remote_dest_folder)  # Create remote_path
        sftp.chdir(remote_dest_folder)
    input_filename = os.path.basename(local_input_filepath)
    sftp.put(local_input_filepath, input_filename)
    logger.info('Sending execution command to {0}:'.format(i))
    logger.info('{0}'.format(cmd))
    stdin, stdout, stderr = client.exec_command(
        'cd {0};'.format(remote_working_dir, cmd))
    for line in stdout:
        logger.info('... ' + line.strip('\n'))
    for line in stderr:
        logger.error('... ' + line.strip('\n'))

    if is_party_2:
        # Get exec file from remote
        sftp.get(remote_exec_filepath, local_dest_folder)
        # Parse execfile in this machine and produce .out file
        exec_filename = os.path.basename(remote_exec_filepath)
        local_exec_filepath = os.path.join(
            local_dest_folder, exec_filename)
        out_filename = os.path.split(exec_filename)[0] + '.out'
        local_out_filepath = os.path.join(
            local_dest_folder, out_filename)
        parse_output(n, d, alg, solution,
            local_out_filepath, local_exec_filepath)

    # Remove .in file from remote (they are too big)
    sftp.remove(input_filename)
    client.close()

    return local_out_filepath if is_party_2 else None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Runs phase 2 experiments. '
        'This script is meant to be run by one of our AWS ubuntu instances as'
        '\'cd secure-distributed-linear-regression/\';'
        '\'python test/test_phase_2_aws.py remote_ip_1 remote_ip_2\'')
    parser.add_argument('remote_ip_1', help='First remote ip address')
    parser.add_argument('remote_ip_2', help='Second remote ip address')

    exec_file = 'bin/test_linear_system'
    dest_folder = 'test/experiments/phase_2/'
    assert os.path.exists(dest_folder), '{0} does not exist.'.format(
        dest_folder)
    assert not os.listdir(dest_folder), '{0} is not empty.'.format(
        dest_folder)
    num_iters_cgd = 15
    num_examples = 5

    args = parser.parse_args()

    ips = [args.remote_ip_1, args.remote_ip_2]
    update_and_compile(ips[0], ips[1])
    update_and_compile(ips[1], ips[0])

    for i in num_examples:
        for alg in ['cgd', 'cholesky']:
            for sigma in [0.1]:
                for d in [10, 20, 50, 100, 200, 500]:
                    for n in [1000, 2000, 5000, 100000, 500000, 1000000]:
                        logger.info(
                            'Running instance: n={0}, d={1}, sigma={2}, alg={3}, num_iters_cgd={4} run={5}'.
                            format(n, d, sigma, alg, num_iters_cgd, i))
                        filename_in = 'test_LS_{0}x{1}_{2}_{3}.in'.format(
                            n, d, sigma, i)
                        filepath_in = os.path.join(
                            dest_folder, filename_in)

                        (X, y, beta) = generate_lin_system_from_regression_problem(
                            n, d, sigma, filepath_in)

                        logger.info('Wrote instance in file {0}'.format(
                                filepath_ls_in))

                        for party in [1, 2]:
                            filename_exec = 'test_LS_{0}x{1}_{2}_{3}_{4}_{5}_p{6}.exec'.format(
                                n, d, sigma, i, alg, num_iters_cgd, party)
                            filepath_exec = os.path.join(
                                dest_folder, filename_exec)

                            cmd = '{0} 1234 {1} {2} {3} {4} > {5}'.format(
                                exec_file,
                                party,
                                filepath_in,
                                alg,
                                num_iters_cgd,
                                filepath_exec)


                            remote_working_dir = 'secure-distributed-linear-regression/'
                            run_instance_remotely(
                                n, d, alg, beta,
                                remote_working_dir,
                                dest_folder, dest_folder,
                                filepath_in, filepath_exec,
                                ips[party - 1], cmd, party == 2)

                            # Remove instance (the get too big)
                            os.system('rm {0}'.format(filepath_in))
                            time.sleep(.5)
