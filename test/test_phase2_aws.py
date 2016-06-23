import os
import argparse
from generate_tests import generate_lin_system_from_regression_problem, objective
import paramiko
import re
import time
import logging
import numpy as np
from math import sqrt, pow

REMOTE_USER = 'ubuntu'
KEY_FILE = '/home/ubuntu/.ssh/id_rsa'

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(message)s')
logger.setLevel(logging.INFO)


def update_and_compile(ip, remote_ip):
    key = paramiko.RSAKey.from_private_key_file(KEY_FILE)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    logger.info('Connecting to {0}:'.format(ip))
    client.connect(hostname=ip, username=REMOTE_USER, pkey=key)

    cmd = 'cd secure-distributed-linear-regression; ' + \
        'pwd; git checkout experiments_phase2; ' + \
        'git pull; make clean; make OBLIVC_PATH=$(cd ../obliv-c && pwd) REMOTE_HOST={0}; killall -9 test_linear_system'.format(remote_ip)
    logger.info('Compiling in {0}:'.format(ip))
    logger.info('{0}'.format(cmd))
    stdin, stdout, stderr = client.exec_command(cmd)
    for line in stdout:
        logger.info('... ' + line.strip('\n'))
    for line in stderr:
        logger.error('... ' + line.strip('\n'))

    client.close()


def parse_output(n, d, X, y, lambda_, alg, solution, condition_number,
        objective_value,
        filepath_out, filepath_exec,
        alg_has_scaling=False):
    """
    Generates a .out file containing accuracy information given
    an .exec file with execution information
    (e.g. intermediate solutions of cgd) for a specific test case.
    """
    with open(filepath_exec, 'r') as f_exec:
        lines = f_exec.readlines()
    cgd_iter_solutions = []
    cgd_iter_gate_sizes = []
    cgd_iter_times = []
    cgd_iter_objective_values = []
    for line in lines:
        """
        The following code relies on the format of the implementation's
        output format for algorithms cgd, cholesky, and ldlt.
        For the version of cgd that has scaling, [alg_has_scaling]
        should be set to true, otherwise intermediate accuracy values
        will not be correct
        """
        m = re.match('OT\s+time:\s*(\S+))', line)
        if m:
            ot_time = float(m.group(1))
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
                    obj_val = objective(X, y, partial_solution, lambda_, n)
                    cgd_iter_objective_values.append(obj_val)
            # Reading intermediate time for cgd
            m = re.match('Iteration\s+([0-9]+)\s+time:\s*(.+)$', line)
            if m:
                cgd_iter_solutions.append(float(m.group(1)))
            # Reading intermediate gate count for cgd
            m = re.match('Iteration\s+([0-9]+)\s+gate\s+count:\s+(.+)$', line)
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
            logger.info('Creating .out file: {}'.format(filepath_out))
            f = open(filepath_out, 'w')
            error = np.linalg.norm(result - solution)
            f.write('n d algorithm ot_time time error gate_count')
            f.write('\n{0} {1} {2} {3} {4} {5} {6}'.format(n, d,
                alg, ot_time, time, error, gate_count))
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
                    error_i = np.linalg.norm(
                        cgd_iter_solutions[i] - solution)
                    f.write('\n{0} {1} {2}'.format(
                        i + 1, error_i, cgd_iter_gate_sizes[i]))
            f.write('\nsolution:')
            f.write('\n{0}'.format(d))
            f.write('\nObjective on solution:')
            f.write('\n{0}'.format(objective_value))
            f.write('\n{0}'.format(' '.join(map(str, solution))))
            f.write('\nresult:')
            f.write('\n{0}'.format(d))
            f.write('\n{0}'.format(' '.join(map(str, result))))
            f.write('\nCondition number:')
            f.write('\n{0}'.format(condition_number))

            f.close()


def run_instance_remotely(n, d, X, y, lambda_, alg, solution, condition_number,
        objective_value,
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
    logger.info('Connecting to {}:'.format(ip))
    #logger.info('Remote working directory: {}'.format(remote_working_dir))
    #logger.info('Remote destination folder: {}'.format(remote_dest_folder))

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=ip, username=REMOTE_USER, pkey=key)
    sftp = client.open_sftp()
    # This function emulates mkdir -p, taken from
    # http://stackoverflow.com/questions/14819681/upload-files-using-sftp-in-python-but-create-directories-if-path-doesnt-exist
    def mkdir_p(sftp, remote_directory):
        """Change to this directory, recursively making new folders if needed.
        Returns True if any folders were created."""
        if remote_directory == '/':
            # absolute path so change directory to root
            sftp.chdir('/')
            return
        if remote_directory == '':
            # top-level relative directory must exist
            return
        try:
            sftp.chdir(remote_directory)  # sub-directory exists
        except IOError:
            dirname, basename = os.path.split(remote_directory.rstrip('/'))
            mkdir_p(sftp, dirname)  # make parent directories
            sftp.mkdir(basename)  # sub-directory missing, so created it
            sftp.chdir(basename)
            return True
    remote_dest_folder = os.path.join(
        'secure-distributed-linear-regression', remote_dest_folder)
    mkdir_p(sftp, remote_dest_folder)
    input_filename = os.path.basename(local_input_filepath)
    sftp.put(local_input_filepath, input_filename)
    logger.info('Executing in {0}:'.format(ip))
    logger.info('{0}'.format(cmd))
    stdin, stdout, stderr = client.exec_command(
        'cd {0}; {1}'.format(remote_working_dir, cmd))
    for line in stdout:
        logger.info('... ' + line.strip('\n'))
    for line in stderr:
        logger.error('... ' + line.strip('\n'))

    if is_party_2:
        # Get exec file from remote and
        # parse it in this machine and produce .out file
        logger.info('Getting file {0} from {1}:'.format(
            remote_exec_filepath, ip))
        exec_filename = os.path.basename(remote_exec_filepath)
        local_exec_filepath = os.path.join(
            local_dest_folder, exec_filename)
        sftp.get(exec_filename, local_exec_filepath)
        out_filename = os.path.splitext(exec_filename)[0] + '.out'
        local_out_filepath = os.path.join(
            local_dest_folder, out_filename)
        parse_output(n, d, X, y, lambda_, alg, solution, condition_number,
            objective_value,
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
    dest_folder = 'test/experiments/phase2/'
    assert os.path.exists(dest_folder), '{0} does not exist.'.format(
        dest_folder)
    assert not os.listdir(dest_folder), '{0} is not empty.'.format(
        dest_folder)
    num_iters_cgd = 15
    num_examples = 4

    args = parser.parse_args()

    ips = [args.remote_ip_1, args.remote_ip_2]
    update_and_compile(ips[0], ips[1])
    update_and_compile(ips[1], ips[0])

    def get_n(d):
        cmax = 10.
        cmin = 1.2
        sigmaY = 0.1
        rand = np.random.random_sample()
        z = (cmax - cmin) * rand  + cmin
        print z
        nmult_num = pow((z - 1) / (z + 1), 2)
        nmult_den = pow(1 - sqrt(1 - (1 + 6 * pow(sigmaY, 2)) / pow((z + 1) / (z - 1), 2)), 2)
        nmult = nmult_num / nmult_den
        n = int(round(nmult * d))*150
        return n

    # This code is to produce a set of tests with a variety of condition numbers,
    # as in the scatter plot in the paper. Domething is wrong with it, 
    # since it should be producing values of n in [1600, 200000]
    # and consition numbers evenly distributed in [1.2,10], but that is not the case
    # c_nums = []
    # for x in range(100):
    #     d = 500
    #     n = get_n(d)
    #     sigma = 0.1
    #     alg = 'cgd'
    #     i = 0
    #     print n
    #     if n > 200000:
    #         continue
    #     #logger.info('Running instance: n={0}, d={1}, sigma={2}, alg={3}, num_iters_cgd={4} run={5}'.
    #     #    format(n, d, sigma, alg, num_iters_cgd, i + 1))
    #     filename_in = 'test_LS_{0}x{1}_{2}_{3}.in'.format(
    #         n, d, sigma, i)
    #     filepath_in = os.path.join(
    #         dest_folder, filename_in)

    #     (X, y, beta, condition_number) = \
    #         generate_lin_system_from_regression_problem(
    #         n, d, sigma, filepath_in)

    #     #logger.info('Wrote instance in file {0}'.format(
    #     #    filepath_in))
    #     print n, condition_number
    #     c_nums.append(condition_number)

    #     #logger.info(condition_number)
    # print sorted(c_nums)

    for i in range(num_examples):
        for alg in ['cgd', 'cholesky']:
            for sigma in [0.1]:
                for d in [10, 20, 50, 100, 200, 500]:
                    for n in [100000]:
                        logger.info(
                            'Running instance: n={0}, d={1}, sigma={2}, alg={3}, num_iters_cgd={4} run={5}'.
                            format(n, d, sigma, alg, num_iters_cgd, i + 1))
                        filename_in = 'test_LS_{0}x{1}_{2}_{3}.in'.format(
                            n, d, sigma, i)
                        filepath_in = os.path.join(
                            dest_folder, filename_in)

                        (X, y, lambda_, beta, condition_number, objective_value) = \
                            generate_lin_system_from_regression_problem(
                                n, d, sigma, filepath_in)

                        logger.info('Wrote instance in file {0}'.format(
                            filepath_in))

                        for party in [1, 2]:
                            filename_exec = 'test_LS_{0}x{1}_{2}_{3}_{4}_{5}_p{6}.exec'.format(
                                n, d, sigma, i, alg, num_iters_cgd, party)
                            filepath_exec = os.path.join(
                                dest_folder, filename_exec)

                            cmd = '{0} 1234 {1} {2} {3} {4} > {5} {6}'.format(
                                exec_file,
                                party,
                                filepath_in,
                                alg,
                                num_iters_cgd,
                                filepath_exec,
                                '&' if party == 1 else '')


                            remote_working_dir = 'secure-distrib   uted-linear-regression/'
                            run_instance_remotely(
                                n, d, X, y, lambda_, alg, beta,
                                condition_number,
                                objective_value,
                                remote_working_dir,
                                dest_folder, dest_folder,
                                filepath_in, filepath_exec,
                                ips[party - 1], cmd, party == 2)
                            time.sleep(.2)

                        # Remove instance (they get too big)
                        logger.info('Deleting file {0}'.format(filepath_in))
                        os.system('rm {0}'.format(filepath_in))
