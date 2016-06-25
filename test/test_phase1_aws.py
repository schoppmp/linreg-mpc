import os
import argparse
import generate_tests as GT
import paramiko
import logging

REMOTE_USER = 'ubuntu'
#KEY_FILE = '/home/ubuntu/.ssh/id_rsa'
KEY_FILE = '/home/agascon/Desktop/experiments1.pem'
USE_PUB_IPS = True

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(message)s')
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Runs phase 1 experiments')
    parser.add_argument(
        '--ips_file', help='public/private config file')

    args = parser.parse_args()

    precision = 56
    num_examples = 5
    exec_file = 'bin/secure_multiplication'
    dest_folder = 'test/experiments/phase1/'
    assert os.path.exists(dest_folder), '{0} does not exist.'.format(
        dest_folder)
    assert not os.listdir(dest_folder), '{0} is not empty.'.format(
        dest_folder)

    if args.ips_file:
        public_ips = []
        private_ips = []
        private_endpoints = []
        with open(args.ips_file, 'r') as f:
            for i, line in enumerate(f.readlines()):
                public_ips.append(line.split()[0])
                private_ips.append(line.split()[1])
                private_endpoints.append(line.split()[1] + ':{0}'.format(
                    1234 + i))
    else:
        public_ips = None
        private_endpoints = None

    def update_and_compile(ip):
        key = paramiko.RSAKey.from_private_key_file(KEY_FILE)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=ip, username=REMOTE_USER, pkey=key)

        cmd_cd = 'cd obliv-c; make CFLAGS=\"-DPROFILE_NETWORK\"; cd ..; ' +\
            'cd secure-distributed-linear-regression; ' +\
            'git stash; git checkout master; git pull; make clean;' +\
            'make OBLIVC_PATH=$(cd ../obliv-c && pwd) bin/secure_multiplication;' +\
            'killall -9 secure_multiplication'
        stdin, stdout, stderr = client.exec_command(cmd_cd)
        for line in stdout:
            print '... ' + line.strip('\n')
        for line in stderr:
            print '... ' + line.strip('\n')

        client.close()

    if public_ips:
        for ip in public_ips:
            update_and_compile(ip)

    def run_remotely(remote_working_dir,
            remote_dest_folder, local_dest_folder,
            local_input_filepath, ip, exec_cmd):

        logger.info('Connecting to {}:'.format(ip))
        key = paramiko.RSAKey.from_private_key_file(KEY_FILE)
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

        # Remove .in file from remote (they are too big)
        sftp.remove(input_filename)
        client.close()

    def retrieve_out_files(party_out_files,
            remote_dest_folder, local_dest_folder):
        for f in party_out_files:
            remote_filepath = os.path.join(remote_dest_folder, f)
            local_filepath = os.path.join(local_dest_folder, f)
            key = paramiko.RSAKey.from_private_key_file(KEY_FILE)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=ip, username=REMOTE_USER, pkey=key)
            sftp = client.open_sftp()
            sftp.get(remote_filepath, local_filepath)
            client.close()


    for n in [1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000]:
        for d in [10, 20, 50, 100, 200, 500]:
            for p in [2, 5, 10, 20]:  # p is number of data providers (not TI)
                if p > d:
                    continue
                logger.info('Running instance n = {0}, d = {1}, p = {2}, run = {3}'.format(
                    n, d, p, num_examples))
                for i in range(num_examples):
                    filename_in = 'test_LR_{0}x{1}_{2}_{3}.in'.format(
                        n, d, p, i)
                    filepath_in = os.path.join(dest_folder, filename_in)
                    (X, y, beta, e) = GT.generate_lin_regression(n, d, 0.1)
                    GT.write_lr_instance(
                        X, y, beta,
                        filepath_in,
                        p,
                        private_endpoints)
                    logger.info('Wrote instance in file {0}'.format(
                        filepath_in))
                    party_exec_files = []
                    for party in range(1, p + 3):
                        filename_exec = 'test_LR_{0}x{1}_{2}_{3}_p{4}.exec'\
                            .format(n, d, p, i, party)
                        filepath_exec = os.path.join(
                            dest_folder, filename_exec)
                        party_exec_files.append(filepath_exec)
                        cmd = '{0} {1} {2} {3} > {4} {5}'.format(
                            exec_file,
                            filepath_in,
                            precision,
                            party,
                            filepath_exec,
                            '&' if party < p + 2 else '')

                        remote_working_dir = 'secure-distributed-linear-regression/'

                        run_remotely(remote_working_dir,
                            dest_folder, dest_folder,
                            filepath_in,
                            public_ips[party - 1]
                            if USE_PUB_IPS else private_ips[party - 1],
                            cmd)

                    retrieve_out_files(party_exec_files, dest_folder)
                    data_parties_times = []
                    for party in range(1, p + 3):
                        with open(party_exec_files[party], 'r') as f:
                            filename_out = os.path.splitext(
                                party_exec_files[party])[0] + '.out'
                            lines = f.readlines()
                            print party, lines
                            if party == 1:  # TI
                                benchmark_decr = lines[0].split() if len(lines[0].split()) == 3 else lines[1]
                                ti_time = float(lines[1].split()[1] if len(lines[0].split()) == 3 else lines[0])
                            else:
                                data_parties_times.append(float(lines[0].split()[1]))
