from votesmart import votesmart
import pandas as pd

votesmart.apikey = 'dc4f937d022863a94d09d5b16be069a5'

nj = votesmart.candidates.getByOfficeState("6", "NJ")
df = pd.DataFrame(pd)
print df 