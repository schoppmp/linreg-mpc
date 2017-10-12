from math import sqrt
import csv
import argparse
import socket
import json

global has_gender
has_gender = -1

def studentize(values):
    n = len(values)
    arith_mean = sum(values)/n
    variance = sqrt(1.0/n * sum([pow(x - arith_mean, 2) for x in values]))
    return ([(x-arith_mean)/variance for x in values], arith_mean, variance)

def load_csv(csv_file, start, end):
    global has_gender
    result = []
    index_of_gender = -1
    with open(csv_file, "r") as f:
        reader = csv.reader(f, delimiter=';')
        for i, inrow in enumerate(reader):
            if i == 0:
                try:
                    index_of_gender = inrow.index("Geschlecht")
                except:
                    pass
                if index_of_gender != -1:
                    if (index_of_gender + 1) >= start and (index_of_gender + 1) <= end:
                        has_gender = 1
                    else:
                        has_gender = 0
            else: 
                outrow = []
                for j, cell in enumerate(inrow):
                    if j != 0:
                        if j-1 >= start and j-1 <= end:
                            if cell == 'm':
                                outrow += [1.0, 0.0]
                            elif cell == 'w':
                                outrow += [0.0, 1.0]
                            else:
                                outrow.append(float(cell))
                        else:
                            if j == index_of_gender:
                                outrow += [0.0, 0.0]
                            else:
                                outrow.append(0.0)
                result.append(outrow)
    return result

def make_csv(outfile, data, csp_ip, e_ip, own_ip, other_ip, start_own, end_own):
    with open(outfile, "w") as f:
        n = len(data)
        m = len(data[0])
        writer = csv.writer(f, delimiter=' ')
        writer.writerow([n, m-1, 2])
        writer.writerow([csp_ip])
        writer.writerow([e_ip])
        if start_own == 0:
            writer.writerow([own_ip, start_own])
            if has_gender == 0:
                writer.writerow([other_ip, end_own+2])
            else:
                writer.writerow([other_ip, end_own+1])
        else:
            writer.writerow([other_ip, 0])
            if has_gender == 1:
                writer.writerow([own_ip, start_own + 1])
            else:
                writer.writerow([own_ip, start_own])
        writer.writerow([n, m-1])
        y_row = []
        for row in data:
            writer.writerow(row[0:-1])
            y_row.append(row[-1])
        writer.writerow([n])
        writer.writerow(y_row)

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Preprocessing script for linreg-mpc")
    parser.add_argument("infile", metavar="in_file", help="csv file to be processed")
    parser.add_argument("outfile", metavar="out_file", help="output file")
    parser.add_argument("csp_ip", metavar="CSP_IP", help="IP of the cryptographic service provider")
    parser.add_argument("e_ip", metavar="EV_IP", help="IP of the evaluator")
    parser.add_argument("own_ip", metavar="own_IP", help="our ip")
    parser.add_argument("other_ip", metavar="other_IP", help="IP of the other data provider")
    parser.add_argument("start", metavar="start", type=int, help="first index of selected features")
    parser.add_argument("end", metavar="end", type=int, help="last index of selected features")

    args = parser.parse_args()
    in_data = load_csv(args.infile, args.start, args.end)

    # transpose
    in_data = [list(x) for x in zip(*in_data)]

    # studentize
    studentized_data = []

    parameters = {
        "means": [],
        "variances": []
    }
    for i, v in enumerate(in_data):
        if any([x != 0.0 for x in v]):
            result = studentize(v)
            studentized_data.append(result[0])
            parameters["means"].append(result[1])
            parameters["variances"].append(result[2])
        else:
            studentized_data.append(v)
            parameters["means"].append(0.0)
            parameters["variances"].append(0.0)    
    # transpose back
    studentized_data = [list(x) for x in zip(*studentized_data)]

    new_params = {}
    
    BUFFER_SIZE = 1024
    if args.start == 0:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        [ip, port] = args.own_ip.split(":")
        s.bind((ip, int(port)))
        s.listen(1)
        print("Waiting for peer...")
        conn, addr = s.accept()
        conn.send(json.dumps(parameters).encode())
        new_params = json.loads(conn.recv(BUFFER_SIZE))
        conn.close()
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        [ip, port] = args.other_ip.split(":")
        try:
            s.connect((ip, int(port)))
        except socket.error as serr:
            print("Start peer first")
            quit()
        
        s.send(json.dumps(parameters).encode())
        new_params = json.loads(s.recv(BUFFER_SIZE))
        s.close()

    for i in range(len(in_data)):
        if parameters["means"][i] == 0.0 and new_params["means"][i] != 0.0:
            parameters["means"][i] = new_params["means"][i]
        if parameters["variances"][i] == 0.0 and new_params["variances"][i] != 0.0:
            parameters["variances"][i] = new_params["variances"][i]

    print("Parameters exchanged")
    with open("params.tmp.json", "w") as jsonfile:
        json.dump(parameters, jsonfile)

    make_csv(args.outfile, studentized_data, args.csp_ip, args.e_ip, args.own_ip, args.other_ip, args.start, args.end)
    print("CSV generated")
