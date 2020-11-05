from bs4 import BeautifulSoup
from votesmart import votesmart
from decouple import config
from collections import OrderedDict
import requests
import json
import pandas as pd
import re
import os.path

class ElectionData:
	states = []
	votesmart.apikey = config('APIKEY')

	def __init__(self, state, out_dir):
		self.getByZip = votesmart.candidates.getByZip
		self.getByOfficeState = votesmart.candidates.getByOfficeState
		self.important_bill_ids = [20653, 26353, 26930, 27188]
		self.billdf = self.create_billdf()
		self.env = votesmart.rating.getSigList(30)
		self.states = self.create_state_list()
		self.offices = votesmart.office.getOfficesByType("C")
		self.candidate_df = self.get_candidates(self.getByOfficeState, {"stateId": state}, True)
		self.out_dir = out_dir

	def create_state_list(self):
		return [s.stateId for s in votesmart.state.getStateIDs()]

	def create_billdf(self):
		important_bills = []
		for item in self.important_bill_ids:
			b = votesmart.votes.getBill(item)
			important_bills += [[item, b.title, b.billNumber, b.dateIntroduced] + [[a.actionId for a in b.actions if a.stage == "Passage"]]]
		return pd.DataFrame(data=important_bills, columns=['bill_id', 'Title', 'Bill_Number', 'Date', 'Actions'])


	def get_votes(self, row):
		allVotes = {}
		for i, bill in enumerate(self.important_bill_ids):
			actions = sum(self.billdf.loc[self.billdf['bill_id'] == bill]['Actions'], [])
			title = self.billdf.loc[self.billdf['bill_id'] == bill].iloc[0]['Title']
			allVotes[title] = []
			for a in actions:
				try:
					action = votesmart.votes.getBillActionVoteByOfficial(a, row['candidateId']).action
					allVotes[title].append(action)
				except:
					pass
		return allVotes

	def get_ratings(self, row):
		ratings = {}
		for i, sig in enumerate(self.env):
			try:
				#most recent rating
				rating = votesmart.rating.getCandidateRating(row["candidateId"], sig.sigId)[-1]
				ratings[rating.ratingName] = {"rating_text": rating.ratingText, "rating_val":rating.rating}
			except:
				pass
		return ratings

	def edit_name(self, name):
		name = re.sub(' [A-Z]. ', ' ', name)
		return name.replace(" ", "_")
    
	def edit_office(self, office, state):
		if office == "President":
			return ""
		elif office == "U.S. House":
			return state
		elif office == "U.S. Senate":
			return "senate"
		else:
			return office.split(" ")[-1]

	def get_positions(self, row):
		URL = "https://www.ontheissues.org/%s/%s.htm" % (self.edit_office(row["office"], row["state"]), self.edit_name(row["name"]))
		page = requests.get(URL)
		soup = BeautifulSoup(page.content, 'html.parser')
		env = None
		try:
			results = soup.find(id="Environment").find_next_siblings()
			env = results[0].find("ul").text.split("\n")
			env = [e.strip() for e in env if len(e) > 0]
		except:
			pass
		return env

	def get_candidates(self, func, params, office, savePath=None):
		all_candidates = []
		if (office):
			for o in self.offices:
				params["officeId"] = o.officeId
				try:    
					candidates = func(**params)
					all_candidates += [[c.ballotName, c.electionOffice, c.officeStateId, c.candidateId] for c in candidates]
				except:
					pass
		else:
			try:
				candidates = func(**params)
				all_candidates += [[c.ballotName, c.electionOffice, c.officeStateId, c.candidateId] for c in candidates]
			except:
				pass
		candidatesdf = pd.DataFrame(data=all_candidates, columns=['name', 'office', 'state', 'candidateId']).drop_duplicates()
		if (not candidatesdf.empty):
			candidatesdf["ratings"] = candidatesdf.apply(self.get_ratings, axis=1)
			candidatesdf["positions"] = candidatesdf.apply(self.get_positions, axis=1)
			candidatesdf["votes"] = candidatesdf.apply(self.get_votes, axis=1)
		if (savePath):
			candidatesdf.to_csv(savePath, encoding="utf-8")
		return candidatesdf

	def create_candidate_profile(self, c):
		try:
			df = self.candidate_df.loc[self.candidate_df['candidateId'] == c.candidateId].to_dict("records")[0]
			df = OrderedDict([(k, df[k]) for k in self.candidate_df.columns.to_list()])
			return df
		except:
			name = "%s %s" % (c.firstName, c.lastName)
			return {"name": name}

	def get_election_data(self, zipcode):
		json_data = OrderedDict({"zip": zipcode, "elections": []})
		#  elections = requests.get("https://www.googleapis.com/civicinfo/v2/elections", params).json()["elections"]
		elections = votesmart.election.getElectionByZip(zipcode)
		for election in elections:
			if election.officeTypeId == "C":
				candidates = votesmart.election.getStageCandidates(election.electionId, "G")
				electionInfo = votesmart.election.getElection(election.electionId)
				date = electionInfo.stages[-1].electionDate
				election_data = OrderedDict([("name", election.name), 
								("date", date),
								("candidates", [])])
				election_data["candidates"] = [self.create_candidate_profile(c) for c in candidates if c.status == "Running"]
				json_data["elections"].append(election_data)
		with open('sample.json', 'w') as f:
			json.dump(json_data, f)
		return json_data
		
	def create_candidate_db(self, limit):
		frames = []
		candidateNames = set()
		i = 0
		while (len(candidateNames) < limit and i < len(self.states)):
			state = self.states[i]
			try:
				candidates = self.get_candidates(self.getByOfficeState, {"stateId":state}, True)
				frames.append(candidates)
				candidateNames.update(candidates["name"].to_list())
			except:
			    pass
			i += 1
		total = pd.concat(frames).drop_duplicates(subset=["name"])
		colOrder = ["name", "office", "state", "candidateId", "ratings", "positions", "votes"]
		data = total[colOrder].to_dict(orient="records")
		with open(os.path.join(self.out_dir, "candidates.json"), "w") as f:
			f.write(json.dumps(data, indent=2))