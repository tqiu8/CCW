from electiondata import ElectionData
import argparse
import os

parser = argparse.ArgumentParser(description='Get election data (default National candidates)')
parser.add_argument('-s', '--state', type=str, required=False, default="NA",
                    help='state of candidates, or "NA" for national candidates')
parser.add_argument('-o', '--out', type=str, required=False, default="test-data",
                    help='output directory')

def main(state, out_dir):
	data = ElectionData(state, out_dir)
	data.create_candidate_db(10)

if __name__ == "__main__":
	args = parser.parse_args()

	print(os.path.join(args.out, "candidates.json"))

	print("Creating  database")
	main(args.state, args.out)