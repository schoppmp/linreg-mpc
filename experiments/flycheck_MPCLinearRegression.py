import re
import csv
import json
import socket
import tempfile
import time
import os
import subprocess
from math import sqrt
from sklearn.linear_model.base import LinearModel

# todo: fix buffer_size for bigger datasets
BUFFER_SIZE = 1024

def studentize(values):
    n = len(values)
    arith_mean = sum(values)/n
    variance = sqrt(1.0/n * sum([pow(x - arith_mean, 2) for x in values]))
    return ([(x-arith_mean)/variance for x in values], arith_mean, variance)

def studentize_matrix(matrix):
    arith_means = []
    variances = []
    for i, row in enumerate(matrix):
        newrow, arith_mean, variance = studentize(row)
        matrix[i] = newrow
        arith_means.append(arith_mean)
        variances.append(variance)
    return (matrix, arith_means, variances)

class MPCLinearRegression(LinearModel):
    def __init__(self, own_ip, other_ip, delimiter=";", category_mappings={"m": [1.0,0.0], "w": [0.0, 1.0]}, mpc_binary_path="../bin/main", mpc_args=["56", "cholesky", "10", "0.001"], debug=False):
        self.own_ip = own_ip
        self.other_ip = other_ip
        self.csp_ip = ""
        self.eval_ip = ""
        self.owned_columns = []
        self.category_columns = []
        self.csv_file = ""
        self.delimiter = delimiter
        self.category_mappings = category_mappings
        self.mpc_binary_path = mpc_binary_path
        self.mpc_args = mpc_args
        self.debug = debug
        self.parameters = {
            "min": -1,
            "arith_means": [],
            "variances": [],
            "length": -1,
        }
        self.other_parameters = {}
        self.result = []

    def parse_csv(self):
        matrix = []
        with open(self.csv_file, "r") as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            for i, row in enumerate(reader):
                if i != 0:
                    newrow = []
                    for j, cell in enumerate(row):
                        if j in self.owned_columns:
                            newrow.append(float(cell))
                        elif j in self.category_columns:
                            newrow += self.category_mappings[cell]
                    matrix.append(newrow)
        return matrix

    def make_csv(self, matrix):
        # if no csp & eval ips set, use first peer for csp, second peer for esp
        print("Generating csv file...")
        if self.parameters["min"] < self.other_parameters["min"]:
            self.csp_ip = self.own_ip.split(":")[0]+":"+str(int(self.own_ip.split(":")[1])+10)
            self.eval_ip = self.other_ip.split(":")[0]+":"+str(int(self.other_ip.split(":")[1])+10)
        else:
            self.csp_ip = self.other_ip.split(":")[0]+":"+str(int(self.other_ip.split(":")[1])+10)
            self.eval_ip = self.own_ip.split(":")[0]+":"+str(int(self.own_ip.split(":")[1])+10)

        n = len(matrix)
        m = len(matrix[0])
        # make temporary file which stays even after closing it
        fd, path = tempfile.mkstemp()
        f = open(path, "w")
        # write parameters
        writer = csv.writer(f, delimiter=' ')
        writer.writerow([n, m-1, 2])
        writer.writerow([self.csp_ip])
        writer.writerow([self.eval_ip])
        if self.parameters["min"] < self.other_parameters["min"]:
            writer.writerow([self.own_ip, 0])
            writer.writerow([self.other_ip, self.parameters["length"]])
        else:
            writer.writerow([self.other_ip, 0])
            writer.writerow([self.own_ip, self.other_parameters["length"]])
        writer.writerow([n, m-1])
        # write matrix
        y_row = []
        for row in matrix:
            writer.writerow(row[0:-1])
            y_row.append(row[-1])
        writer.writerow([n])
        writer.writerow(y_row)
        f.close()
        os.close(fd)
        print("csv file generated: " + path)
        return path

    def exchange_parameters(self):
        if int(self.own_ip.split(":")[1]) < int(self.other_ip.split(":")[1]):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            [ip, port] = self.own_ip.split(":")
            s.bind((ip, int(port) + 20))
            s.listen(1)
            print(self.own_ip + " waiting for peer " + self.other_ip)
            conn, addr = s.accept()
            conn.send(json.dumps(self.parameters).encode())
            self.other_parameters = json.loads(conn.recv(BUFFER_SIZE).decode('utf-8'))
            conn.close()
            s.close()
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            [ip, port] = self.other_ip.split(":")
            print(self.own_ip + " waiting for peer " + self.other_ip)
            while True:
                try:
                    s.connect((ip, int(port) + 20))
                    break
                except socket.error as serr:
                    time.sleep(1)
                    s.close()
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.send(json.dumps(self.parameters).encode())
            self.other_parameters = json.loads(s.recv(BUFFER_SIZE).decode('utf-8'))
            s.close()
        print("Parameters exchanged")

    def calculate_matrix(self):
        matrix = self.parse_csv()
        # transpose
        matrix = [list(x) for x in zip(*matrix)]
        matrix, self.parameters["arith_means"], self.parameters["variances"] = studentize_matrix(matrix)

        self.parameters["length"] = len(matrix)
        self.exchange_parameters()

        # fill matrix with zeros for parts that are owned by the peer
        if self.parameters["min"] > self.other_parameters["min"]:
            matrix = [[0.0] * len(matrix[0])] * self.other_parameters["length"] + matrix
        else:
            matrix = matrix + [[0.0] * len(matrix[0])] * self.other_parameters["length"]
            
        # transpose back
        return [list(x) for x in zip(*matrix)]
    
    def fit(self, csv_file, owned_columns):
        # setup
        self.owned_columns = []
        self.category_columns = []
        for val in owned_columns.split():
            m = re.search("(c?)([0-9]+)", val)
            if m.group(1) == "c":
                self.category_columns.append(int(m.group(2)))
            else:
                self.owned_columns.append(int(m.group(0)))
        self.csv_file = csv_file
        self.parameters["min"] = min(self.owned_columns + self.category_columns)
        # this len is wrong!
        # self.parameters["length"] = len(self.owned_columns) + 2 * len(self.category_columns)        
        matrix = self.calculate_matrix()
        temp_path = self.make_csv(matrix)

        if not os.path.exists(self.mpc_binary_path):
            print("Can't find mpc binary!")
            return

        # start mpc binary
        cmd = [self.mpc_binary_path, temp_path, self.mpc_args[0], "3"] + self.mpc_args[1:]
        outputfd = None if self.debug else subprocess.DEVNULL
        # TODO: error handling
        # TODO: handle when subprocess aborts unnormally and kill it so the socket is freed
        # TODO: open tcp connection only once...
        if self.parameters["min"] < self.other_parameters["min"]:
            print("Starting DP1 on " + self.own_ip)
            cmd[3] = "3"
            subprocess.Popen(cmd, stdout=outputfd)
            print("Starting CSP on " + self.csp_ip)
            cmd[3] = "1"
            subprocess.Popen(cmd, stdout=outputfd)
            
            # getting the result
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            [ip, port] = self.own_ip.split(":")
            s.bind((ip, int(port) + 30))
            s.listen(1)
            print("Waiting for result...")
            conn, addr = s.accept()
            self.result = json.loads(conn.recv(BUFFER_SIZE).decode("utf-8"))
            conn.close()
            s.close()
        else:
            print("Starting DP2 on " + self.own_ip)
            cmd[3] = "4"
            subprocess.Popen(cmd, stdout=outputfd)
            print("Starting EVAL on " + self.eval_ip)
            cmd[3] = "2"
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            output, _ = process.communicate()
            if self.debug:
                print(output.decode("UTF-8"))
            self.result = [float(x) for x in re.findall("-?[0-9]+.[0-9]+", output.splitlines()[-1].decode("UTF-8"))]
            
            # sending result
            print("Sending result...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            [ip, port] = self.other_ip.split(":")
            s.connect((ip, int(port) + 30))
            s.send(json.dumps(self.result).encode())
            s.close()
        if self.debug:
            print("Results: ", self.result)
        else:
            # delete temporary file if we are not in debug
            os.remove(temp_path)

    def predict(self, X):
        if self.result == []:
            print("Please fit a model first!")
            return -1
        # todo handle inputting "m" or "w"
        means = []
        variances = []
        if self.parameters["min"] < self.other_parameters["min"]:
            means = self.parameters["arith_means"] + self.other_parameters["arith_means"]
            variances = self.parameters["variances"] + self.other_parameters["variances"]
        else:
            means = self.other_parameters["arith_means"] + self.parameters["arith_means"]
            variances = self.other_parameters["variances"] + self.parameters["variances"]
        if self.debug:
            print("means: ", means)
            print("variances: ", variances)
            print("coefficients: ", self.result)
        result = 0
        for i, x in enumerate(X):
            result += ((x-means[i]) / variances[i]) * self.result[i]
        return result * variances[-1] + means[-1]
