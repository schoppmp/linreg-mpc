import os
import argparse
import generate_tests as GT
import paramiko
import logging
import re

REMOTE_USER = 'ubuntu'
KEY_FILE = '/home/ubuntu/.ssh/id_rsa'
# Set to True to run this script from a machine outside AWS
USE_PUB_IPS = False
# Set to True to rerun existing instances
RECOMPUTE = False


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(message)s')
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Runs phase 1 experiments')
    parser.add_argument(
        '--ips_file', help='public/private config file')

    args = parser.parse_args()

    precision = 56
    num_examples = 3
    exec_file = 'bin/secure_multiplication'
    dest_folder = 'test/experiments/phase1/'
    assert os.path.exists(dest_folder), '{0} does not exist.'.format(
        dest_folder)
    #assert not os.listdir(dest_folder), '{0} is not empty.'.format(
    #    dest_folder)

    if args.ips_file:
        public_ips = []
        private_ips = []
        private_endpoints = []
        with open(args.ips_file, 'r') as f:
            for i, line in enumerate(f.readlines()):
                if not line.strip(): continue
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

        logger.info('Compiling in {0}'.format(ip))



        cmd_network_profiling = 'cd obliv-c; make clean; make RELEASE=1 CFLAGS=\"-DPROFILE_NETWORK\"; cd ..; ' +\
            'cd secure-distributed-linear-regression; ' +\
            'git stash; git checkout master; git pull; make clean;' +\
            'git submodule update --init --recursive;' +\
            'cd lib/absentminded-crypto-kit/;' +\
            'make OBLIVC_PATH=$(cd ../../../obliv-c && pwd);' +\
            'cd ../..;' +\
            'make OBLIVC_PATH=$(cd ../obliv-c && pwd) bin/secure_multiplication;' +\
            'killall -9 secure_multiplication'

        cmd_compile = 'cd obliv-c; make clean; make RELEASE=1; cd ..; ' +\
            'cd secure-distributed-linear-regression; ' +\
            'git stash; git checkout master; git pull; make clean;' +\
            'git submodule update --init --recursive;' +\
            'cd lib/absentminded-crypto-kit/;' +\
            'make OBLIVC_PATH=$(cd ../../../obliv-c && pwd);' +\
            'cd ../..;' +\
            'make OBLIVC_PATH=$(cd ../obliv-c && pwd) bin/secure_multiplication;' +\
            'killall -9 secure_multiplication; ' +\
            'rm secure-distributed-linear-regression/test/experiments/phase1/*'

        cmd_dont_compile = 'killall -9 secure_multiplication; ' +\
              'rm secure-distributed-linear-regression/test/experiments/phase1/*'
        stdin, stdout, stderr = client.exec_command(cmd_compile)
        for line in stdout:
            print '... ' + line.strip('\n')
        for line in stderr:
            print '... ' + line.strip('\n')

        client.close()

    for ip in (public_ips if USE_PUB_IPS else private_ips):
        pass #update_and_compile(ip)

    def run_remotely(remote_working_dir,
            remote_dest_folder, local_dest_folder,
            local_input_filepath, ip, exec_cmd):

        logger.info('Connecting to {}...'.format(ip))
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
        logger.info('Copying {0} to {1}...'.format(local_input_filepath, ip))
        #sftp.put(local_input_filepath, input_filename)
        scp_cmd = 'scp {0} {1}:{2}'.format(local_input_filepath, ip, remote_dest_folder)
        logger.info(scp_cmd)
        os.system(scp_cmd)
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
        for i, f in enumerate(party_out_files):
            ip = public_ips[i] if USE_PUB_IPS else private_ips[i]
            key = paramiko.RSAKey.from_private_key_file(KEY_FILE)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=ip, username=REMOTE_USER, pkey=key)
            sftp = client.open_sftp()
            sftp.chdir(os.path.join('secure-distributed-linear-regression',
                remote_dest_folder))
            logger.info(
                'Retrieving .exec file {0} from {1} in {2}'.format(
                    f, remote_dest_folder, ip))
            sftp.get(f, os.path.join(local_dest_folder, f))
            client.close()

    for i in range(num_examples):
        for d in [10, 20, 50, 100, 200]:#, 500]:
            for p in [2, 3, 5]: #, 10, 20]:  # p is number of data providers (not TI)
                if p > d:
                    continue
                for n in [1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000]:
                    logger.info('Running instance n = {0}, d = {1}, p = {2}, run = {3}'.format(
                        n, d, p, i))

                    party_exec_files = []
                    party_out_files = []
                    for party in range(1, p + 3):
                        filename_exec = 'test_LR_{0}x{1}_{2}_{3}_p{4}.exec'\
                            .format(n, d, p, i, party)
                        filepath_exec = os.path.join(
                            dest_folder, filename_exec)
                        party_exec_files.append(filename_exec)
                        party_out_files.append(os.path.splitext(
                            filename_exec)[0] + '.out')

                    party_out_filepaths = map(lambda x: os.path.join(dest_folder, x), party_out_files)
                    if all([os.path.exists(party_out_filepaths[j - 1]) for j in range(1, p + 3)]) and\
                       not RECOMPUTE:
                        logger.info('Files {} exist. Skipping instance.'.format(', '.join(party_out_files)))
                        continue

                    filename_in = 'test_LR_{0}x{1}_{2}_{3}.in'.format(
                        n, d, p, i)
                    filepath_in = os.path.join(dest_folder, filename_in)
                    if RECOMPUTE or not os.path.exists(filepath_in):
                        logger.info('Generating instance...')
                        (X, y, beta, e) = GT.generate_lin_regression(n, d, 0.1)
                        logger.info('Writing instance...')
                        GT.write_lr_instance(
                            X, y, beta,
                            filepath_in,
                            p,
                            private_endpoints)
                        logger.info('Wrote instance in file {0}'.format(
                            filepath_in))
                    else:
                        logger.info('Instance in file {0} exists. No need to generate it.'.format(
                            filepath_in))

                    for party in range(1, p + 3):
                        cmd = '{0} {1} {2} {3} > {4} 2>&1 {5}'.format(
                            exec_file,
                            filepath_in,
                            precision,
                            party,
                            os.path.join(dest_folder, party_exec_files[party - 1]),
                            '&' if party < p + 2 else '')
                        
                        remote_working_dir = 'secure-distributed-linear-regression/'

                        run_remotely(remote_working_dir,
                            dest_folder, dest_folder,
                            filepath_in,
                            public_ips[party - 1]
                            if USE_PUB_IPS else private_ips[party - 1],
                            cmd)

                    logger.info('All parties running.')

                    retrieve_out_files(party_exec_files,
                        dest_folder, dest_folder)
                    for j, filename_exec in enumerate(party_exec_files):
                        data_parties_byte_count = []
                        data_parties_flush_count = []
                        filepath_exec = os.path.join(
                            dest_folder, filename_exec)
			filepath_out = os.path.join(
			    dest_folder, party_out_files[j])
                        f_exec = open(filepath_exec, 'r')
                        f_out = open(filepath_out, 'w')
                        logger.info('Writing .out file {0}'.format(filepath_out))
			for line in f_exec.readlines():
                            if line.startswith('{'):
				f_out.write(line)
                            m = re.match('Total bytes sent: (\d+)', line)
                            if m:
				data_parties_byte_count.append(m.group(1))
                            m = re.match('Total flush done: (\d+)', line)
                            if m:
				data_parties_flush_count.append(m.group(1))
                        f_out.write('[{}]\n'.format(', '.join(data_parties_byte_count)))
                        f_out.write('[{}]\n'.format(', '.join(data_parties_flush_count)))
                        f_exec.close()
                        f_out.close()
                    os.remove(filepath_in)
