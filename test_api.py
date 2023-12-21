# %%

import requests
import uuid

# Generate a UID
uid = str(uuid.uuid4())

#%%

# Define the API endpoint
endpoint = "https://rmi-in-a-box.politemushroom-551f150f.westus2.azurecontainerapps.io/ask"
#endpoint = "http://localhost:8001/ask"

# The query you want to ask
data = {
    "uid": "55", #uid,
    "query": "Explain downstream oil emissions"
}

# Make a POST request
response = requests.post(endpoint, json=data)

# Check the response
print(response.json())
#print(len(response.json()['chat_history']))

#%%
