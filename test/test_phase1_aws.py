import os
import argparse
from generate_tests import (generate_lin_regression, write_lr_instance)
import paramiko

REMOTE_USER = 'ubuntu'
KEY_FILE = '/home/ubuntu/.ssh/id_rsa'

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Runs phase 1 experiments')
    parser.add_argument('exec_file', help='Executable')
    #parser.add_argument('n', help='Number of records', type=int)
    #parser.add_argument('d', help='Number of features', type=int)
    #parser.add_argument('p', help='Number of parties', type=int)
    parser.add_argument('dest_folder', help='Destination folder')
    parser.add_argument(
        'num_examples', help='Number of executions of every setting', type=int)
    parser.add_argument(
        '--verbose', '-v', action='store_true', help='Run in verbose mode')
    parser.add_argument(
    	'--ips_file', help='public/private config file', required=False)

    args = parser.parse_args()
    VERBOSE = args.verbose
    #assert args.p <= args.d

    if args.ips_file:
        public_ips = []
        private_endpoints = []
        with open(args.ips_file, 'r') as f:
            for i, line in enumerate(f.readlines()):
                public_ips.append(line.split()[1])
                private_endpoints.append(line.split()[1] + ':{0}'.format(1234 + i))
    else:
        public_ips = None
        private_endpoints = None

    def update_and_compile(ip):
        key = paramiko.RSAKey.from_private_key_file(KEY_FILE)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=ip, username=REMOTE_USER, pkey=key)

        cmd_cd = 'cd secure-distributed-linear-regression; pwd; git stash; git checkout phase1; git pull; make bin/secure_multiplication; killall -9 secure_multiplication'
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
        stdin, stdout, stderr = client.exec_command(cmd)#+'; sleep 1;'+killall secure_multiplication')
        for line in stdout:
            print '... ' + line.strip('\n')
        for line in stderr:
            print '... ' + line.strip('\n')

        client.close()

    def retrieve_out_files(party_out_files):
        for f in party_out_files:
            key = paramiko.RSAKey.from_private_key_file(KEY_FILE)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname = ip, username=REMOTE_USER, pkey=key)
            sftp = client.open_sftp()
            sftp.get(f, f)

    #for n, d in [(2000, 20), (10000, 100), (50000, 500)]:
    for n, d in [(50000, 500)]:
        for p in [3, 4, 2]:  # p is number of data providers (not TI)
            if p > d:
                continue
            print n,d,p
            for i in range(args.num_examples):
                filename_lr_in = 'test_LR_{0}x{1}_{2}_{3}.in'.format(n, d, p, i)
                filepath_lr_in = os.path.join(args.dest_folder, filename_lr_in)
                # This corresponds to an experiment setup as in Nikolaenloks S&P paper:
                # "Privacy-Preserving Ridge Regression on Hundreds of Millions of Records"
                (X, y, beta, e) = generate_lin_regression(n, d)
                write_lr_instance(X, y, beta, filepath_lr_in, p, private_endpoints)
                if VERBOSE:
                    print('Wrote instance in file {0}'.format(filepath_lr_in))
                party_out_files = []
                for party in range(p+1):
                    filename_lr_out = 'test_LR_{0}x{1}_{2}_{3}_p{4}.out'.format(n, d, p, i, party)
                    filepath_lr_out = os.path.join(args.dest_folder, filename_lr_out)
                    party_out_files.append(filepath_lr_out)
                    cmd = '{0} {1} {2} > {3} {4}'.format(args.exec_file, filepath_lr_in, party, filepath_lr_out, '&' if party < p else '')
                    if args.ips_file:
                        run_remotely(args.dest_folder, filepath_lr_in, filename_lr_in, public_ips[party], cmd)
                    else:
                        #print cmd
                        os.system(cmd)
                data_parties_times = []
                if args.ips_file:
                    continue#retrieve_out_files(party_out_files)
                for party in range(p+1):
                    with open(party_out_files[party], 'r') as f:
                        lines = f.readlines()
                        #print party, lines
                        if party == 0: # TI
                            assert len(lines) == 2, lines
                            benchmark_decr = lines[0].split() if len(lines[0].split()) == 3 else lines[1]
                            ti_time = float(lines[1].split()[1] if len(lines[0].split()) == 3 else lines[0])
                        else:
                            data_parties_times.append(float(lines[0].split()[1]))
                #print 'n = {0} d = {1}, p = {2}'.format(
                #    benchmark_decr[0],
                #    benchmark_decr[1],
                #    benchmark_decr[2])
                #print 'TI time (s): {0}'.format(ti_time)
                #print 'Data parties times (s): {0}'.format(data_parties_times)
                #print 'Data parties AVG time (s): {0}'.format(reduce(lambda x,y:x+y, data_parties_times)/p)
                #print '*'.format(30)
                print 'n = {0}, d = {1}, p = {2}, TI_time = {3}, data_parties_times = {4}, data_parties_avg_time = {5}'.format(
                    benchmark_decr[0],
                    benchmark_decr[1],
                    benchmark_decr[2],
                    ti_time,
                    data_parties_times,
                    reduce(lambda x, y: x + y, data_parties_times) / p)
