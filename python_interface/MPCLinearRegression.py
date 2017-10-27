import re
import csv
import json
import socket
import tempfile
import time
import os
import subprocess
from math import isnan
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
    """
    Secure linear regression with another party (semi-honest).
    """
    def __init__(self, own_ip, other_ip, delimiter=";", category_mappings={"m": [1.0], "w": [0.0]},
                 mpc_binary_path="../bin/main", mpc_args=["56", "cholesky", "10", "0.001"], debug=False):
        self.own_ip = own_ip
        self.other_ip = other_ip
        self.csp_ip = ""
        self.eval_ip = ""
        self.csv_file = ""
        self.delimiter = delimiter
        self.category_mappings = category_mappings
        self.mpc_binary_path = mpc_binary_path
        self.mpc_args = mpc_args
        self.debug = debug
        self.parameters = {
            "is_last": False,
            "arith_means": [],
            "variances": [],
            "length": -1,
            "owned_columns": [],
        }
        self.other_parameters = {}
        self.result = []

    def parse_csv(self, csv_file):
        """
        parse the csv input file and extract owned data
        """
        matrix = []
        with open(csv_file, "r") as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            for i, row in enumerate(reader):
                newrow = []
                for j, (is_category, index, name) in enumerate(self.parameters["owned_columns"]):
                    cell = row[index]    
                    if i == 0:
                        self.parameters["owned_columns"][j] = (is_category, index, cell.strip())
                    else:
                        if is_category > 0:
                            if self.parameters["is_last"] and len(self.category_mappings[cell]) > 1 and j == (len(self.parameters["owned_columns"]) - 1):
                                raise Exception("Result column can't be a category feature")
                            newrow += self.category_mappings[cell]
                            self.parameters["owned_columns"][j] = (len(self.category_mappings[cell]), index, name)
                        else:
                            newrow.append(float(cell))
                if newrow != []:
                    matrix.append(newrow)
        return matrix

    def make_csv(self, matrix):
        """
        Create the csv that is fed into the mpc binary
        """
        # if no csp & eval ips set, use first peer for csp, second peer for esp
        print("Generating csv file...")
        if not self.parameters["is_last"]:
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
        if not self.parameters["is_last"]:
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
        """
        exchange needed parameters with peer
        """
        if int(self.own_ip.split(":")[1]) < int(self.other_ip.split(":")[1]):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                [ip, port] = self.own_ip.split(":")
                s.bind((ip, int(port) + 20))
                s.listen(1)
                print(self.own_ip + " waiting for peer " + self.other_ip)
                conn, _ = s.accept()
                conn.send(json.dumps(self.parameters).encode())
                self.other_parameters = json.loads(conn.recv(BUFFER_SIZE).decode('utf-8'))
            finally:
                conn.close()
                s.close()
        else:
            print(self.own_ip + " waiting for peer " + self.other_ip)
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    [ip, port] = self.other_ip.split(":")
                    s.connect((ip, int(port) + 20))
                    s.send(json.dumps(self.parameters).encode())
                    self.other_parameters = json.loads(s.recv(BUFFER_SIZE).decode('utf-8'))
                    s.close()
                    break
                except socket.error as serr:
                    # try here fixes 
                    try:
                        time.sleep(1)
                    finally:
                        s.close()
                finally:
                    s.close()
        if not (self.parameters["is_last"] != self.other_parameters["is_last"]):
            raise Exception("Two result columns or no result columns specified")
        print("Parameters exchanged")

    def calculate_matrix(self):
        """
        calculate the input matrix for linear regression from the parsed csv file
        """
        matrix = self.parse_csv(self.csv_file)
        # transpose
        matrix = [list(x) for x in zip(*matrix)]
        matrix, self.parameters["arith_means"], self.parameters["variances"] = studentize_matrix(matrix)

        self.parameters["length"] = len(matrix)
        self.exchange_parameters()

        # fill matrix with zeros for parts that are owned by the peer
        if self.parameters["is_last"]:
            matrix = [[0.0] * len(matrix[0])] * self.other_parameters["length"] + matrix
        else:
            matrix = matrix + [[0.0] * len(matrix[0])] * self.other_parameters["length"]
            
        # transpose back
        return [list(x) for x in zip(*matrix)]

    def run_mpc(self, path):
        """ 
        starts the mpc binary to securely calculate the linear regression model with peer
        """
        cmd = [self.mpc_binary_path, path, self.mpc_args[0], "3"] + self.mpc_args[1:]
        outputfd = None if self.debug else subprocess.DEVNULL
        # TODO: handle when subprocess aborts unnormally and kill it so the socket is freed
        if not self.parameters["is_last"]:            
            print("Starting DP1 on " + self.own_ip)
            cmd[3] = "3"
            subprocess.Popen(cmd, stdout=outputfd)
            print("Starting CSP on " + self.csp_ip)
            cmd[3] = "1"
            subprocess.Popen(cmd, stdout=outputfd)
            
            # getting the result
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                [ip, port] = self.own_ip.split(":")
                s.bind((ip, int(port) + 30))
                s.listen(1)
                print("Waiting for result...")
                conn, _ = s.accept()
                self.result = json.loads(conn.recv(BUFFER_SIZE).decode("utf-8"))
            finally:
                try:
                    conn.close()
                except UnboundLocalError:
                    pass
                s.close()
            print("Got result.")
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
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    [ip, port] = self.other_ip.split(":")
                    s.connect((ip, int(port) + 30))
                    s.send(json.dumps(self.result).encode())
                    break
                except socket.error:
                    try:
                        time.sleep(1)
                    finally:
                        s.close()
                finally:
                    s.close()
            print("Sent result.")


    def make_matrix(self, csv_file, owned_columns):
        """
        setup parameters and calculate matrix
        """
        self.parameters["owned_columns"] = []
        result_col = None
        is_last = False
        for val in owned_columns.split():
            m = re.search("(r?c?)([0-9]+)", val)
            if m.group(1) == "c":
                self.parameters["owned_columns"].append((1, int(m.group(2)), ""))
            elif m.group(1) == "rc":
                is_last = True
                result_col = (1, int(m.group(2)), "")
            elif m.group(1) == "r":
                is_last = True
                result_col = (0, int(m.group(2)), "")
            else:
                self.parameters["owned_columns"].append((0, int(m.group(0)), ""))
        # if there is a result column it must be the last
        if not result_col is None:
            self.parameters["owned_columns"].append(result_col)
        self.csv_file = csv_file
        self.parameters["is_last"] = is_last
        return self.calculate_matrix()
                   
    def fit(self, csv_file, owned_columns):
        """
        Take CSV data, columns we own and securely calculate linear
        regression parameters with other party
        """
        temp_path = self.make_csv(self.make_matrix(csv_file, owned_columns))
      
        if not os.path.exists(self.mpc_binary_path):
            raise Exception("Can't find mpc binary!")

        self.run_mpc(temp_path)
        
        if self.debug:
            print("Results: ", self.result)
        else:
            # delete temporary file if we are not in debug
            os.remove(temp_path)
        
    def predict(self, X):
        """
        predict based on the previously learned linear regression model.
        You can specify the values as a dict with the csv's column names as keys
        or as a list ordered after the columns. If you specify a value with "NaN"
        it will get filled with the training data's mean value for that column.
        """
        if self.result == []:
            raise Exception("Please fit a model first!")
        result_col = None
        means = []
        variances = []
        columns = []
        if not self.parameters["is_last"]:
            means = self.parameters["arith_means"] + self.other_parameters["arith_means"]
            variances = self.parameters["variances"] + self.other_parameters["variances"]
            columns = self.parameters["owned_columns"] + self.other_parameters["owned_columns"]
        else:
            means = self.other_parameters["arith_means"] + self.parameters["arith_means"]
            variances = self.other_parameters["variances"] + self.parameters["variances"]
            columns = self.other_parameters["owned_columns"] + self.parameters["owned_columns"]

        # fixes json looses tuple structure
        columns = [tuple(x) for x in columns]
        if self.debug:
            print("means: ", means)
            print("variances: ", variances)
            print("columns: ", columns)
            print("coefficients: ", self.result)
        if len(means) != len(variances):
            raise Exception("Length of means != length of variances. This should not happen.")

        ordered_X = [None] * (len(columns))

        if isinstance(X, dict):
            for i, (is_category, index, col_name) in enumerate(columns[:-1]):
                if is_category > 0:
                    ordered_X[i] = self.category_mappings[X[col_name]]
                else:
                    ordered_X[i] = float(X[col_name])  
        elif isinstance(X, list):
            mapping = [(i, index) for i, (_, index, _) in enumerate(columns[:-1])]
            mapping.sort(key=lambda x: x[1])

            for (x, (index, _)) in zip(X, mapping):
                try:
                    ordered_X[index] = float(x)
                except ValueError:
                    ordered_X[index] = self.category_mappings[x]
        else:
            raise Exception("input must be a dict or a list")

        result_col = columns[-1]
        # flatten list
        tmp = []
        for x in ordered_X:
            if x is None:
                continue
            if isinstance(x, list):
                tmp += x
            else:
                tmp.append(x)
        # replace nans with means
        ordered_X = [means[i] if isnan(x) else x for i,x in enumerate(tmp)]
        
        if self.debug:
            print("X ordered:", ordered_X)
        result = 0
        for i, x in enumerate(ordered_X):
            result += ((x-means[i]) / variances[i]) * self.result[i]
        return result * variances[-1] + means[-1]
