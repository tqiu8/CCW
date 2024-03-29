from electiondata import ElectionData
import argparse
import os

parser = argparse.ArgumentParser(description='Get election data (default National candidates)')
parser.add_argument('-s', '--state', type=str, required=False, default="NA",
                    help='state of candidates, or "NA" for national candidates')
parser.add_argument('-o', '--out', type=str, required=False, default="test-data",
                    help='output directory')
parser.add_argument('-a', '--analysis', type=bool, required=False, default=False,
										help='enable analysis of candidate data')

def main(state, out_dir, analysis):
	data = ElectionData(state, out_dir)
	data.format_candidates()

if __name__ == "__main__":
	args = parser.parse_args()

	print("Creating database")
	main(args.state, args.out, args.analysis)