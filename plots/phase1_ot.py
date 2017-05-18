from matplotlib import rc, pyplot as plt
import numpy as np
import os
import sys
import json
from datetime import timedelta

ns = [i * 10**j for j in [3,4,5] for i in [1,2,5]]# + [1000000]
ds = [10, 20, 50, 100]#, 200, 500]
num_samples = 1
ps = [2,3,5]#[1, 2, 5, 10, 20]

# n x d x num_parties x sample x party x (32 or 64)-> (cputime, waittime, realtime, bytes sent, flush count)
data = np.zeros((len(ns), len(ds), len(ps), num_samples, max(ps)+2, 2, 5), dtype=np.float64)
data[:] = np.NAN

def format_hms(t):
    seconds = int(round(t))
    hours = seconds / 3600;
    minutes = seconds / 60;
    result = "{}s".format(seconds % 60)
    if minutes > 0:
        result = "{}m".format(minutes % 60) + result
    if hours > 0: 
        result = "{}h".format(hours) + result
    return result

for i_n, n in enumerate(ns):
    for i_d, d in enumerate(ds):
        if d == 500 and n == 1000000:
            continue
        for i_p, num_parties in enumerate(ps):
            for sample in xrange(num_samples):
                for party in xrange(num_parties+2): 
                    try:
                        filename = "../experiments/results/phase1_ot_64/test_LR_{}x{}_{}_{}_ot_p{}.out".format(n, d, num_parties, sample, party+1)
                        lines = open(filename).read().splitlines()
                        if party == 0:
                            lines = lines[1:] # ignore first line for CSP (contains only info we already know)
                        current_data = json.loads(lines[0]) # TODO make sure that the times are on the first line
                        data[i_n, i_d, i_p, sample, party, 0, :3] = [current_data[key] for key in ['cputime', 'wait_time', 'realtime']]
                        data[i_n, i_d, i_p, sample, party, 0, 3] = np.sum(np.fromstring(lines[1][1:-1], sep=',')) # bytes sent
                        
                        # 32 bits
                        filename = "../experiments/results/phase1_ot_32/test_LR_{}x{}_{}_{}_ot_p{}.out".format(n, d, num_parties, sample, party+1)
                        lines = open(filename).read().splitlines()
                        if party == 0:
                            lines = lines[1:] # ignore first line for CSP (contains only info we already know)
                        current_data = json.loads(lines[0]) # TODO make sure that the times are on the first line
                        data[i_n, i_d, i_p, sample, party, 1, :3] = [current_data[key] for key in ['cputime', 'wait_time', 'realtime']]
                        data[i_n, i_d, i_p, sample, party, 1, 3] = np.sum(np.fromstring(lines[1][1:-1], sep=',')) # bytes sent
                    except TypeError, e:
                        #pass
                         print filename, e

# cpu + running time
for i_n, n in enumerate(ns):
    sys.stdout.write("\midrule\n\\multirow{%d}{*}{%d}\n" % (len(ds),n))
    for i_d, d in enumerate(ds):
        if d == 500 and n == 1000000:
            continue
        #if i_d != 0:
        #    sys.stdout.write(10 * " ")
        sys.stdout.write("& {:<10d}".format(d))
        for i_p, num_parties in enumerate(ps):
            for i_bits in [0, 1]:
                #time_ti = np.nanmean(data[i_n, i_d, i_p, :, 0, 0])
                time_parties = np.nanmean(data[i_n, i_d, i_p, :, 2:, i_bits, 2])
                #time_total = np.nanmean(data[i_n, i_d, i_p, :, num_parties+1, 2])
                #sys.stdout.write("& {:9.3f} & {:9.3f}  & {:9.3f} ".format(time_ti, time_parties, time_total))
                sys.stdout.write("& {:10s}".format(format_hms(time_parties)))
        sys.stdout.write("\\\\\n")
