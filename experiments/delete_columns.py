import csv
import argparse

def delete_columns(infile, outfile, selected):
    with open(infile, "r") as fin, open(outfile, "w") as fout:
        reader = csv.reader(fin, delimiter=';')
        writer = csv.writer(fout, delimiter=';')
        for row in reader:
            writer.writerow([x for i, x in enumerate(row) if i not in selected])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete columns from csv file")
    parser.add_argument("infile", metavar="in_file", help="csv file to be processed")
    parser.add_argument("outfile", metavar="out_file", help="output file")
    parser.add_argument("selected", metavar="selected", nargs="+", type=int,  help="columns to delete")

    args = parser.parse_args()
    delete_columns(args.infile, args.outfile, args.selected)
