import json
import argparse

def destudentize(val, mean, variance):
    return (val + mean) * variance


if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Postprocessing script for linreg-mpc")
    parser.add_argument("results", metavar="results", type=float, nargs="+", help="results of mpc")
    args = parser.parse_args()

    dest_results = []
    with open("params.tmp.json", "r") as jsonfile:
        parameters = json.load(jsonfile)
        for i, v in enumerate(args.results):
            dest_results.append(v, parameters["means"][i], parameters["variances"][i])
    print(dest_results)
