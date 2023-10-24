#%%%

import requests

# Define the API endpoint
endpoint = "http://localhost:5000/ask"

# The query you want to ask
data = {"query": "Which region is Bhutan in?"}

# Make a POST request
response = requests.post(endpoint, json=data)

# Check the response
print(response.json())

#%%
