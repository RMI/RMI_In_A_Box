#%%%

# import requests

# # Define the API endpoint
# endpoint = "http://localhost:5000/ask"

# # The query you want to ask
# data = {"query": "Summarize the document titled a climate resilient future?"}

# # Make a POST request
# response = requests.post(endpoint, json=data)

# # Check the response
# print(response.json())

# #%%

# import requests

# # Define the API endpoint
# endpoint = "https://rmi-in-a-box.politemushroom-551f150f.westus2.azurecontainerapps.io/ask"

# # The query you want to ask
# data = {"query": "Summarize the document titled a climate resilient future?"}

# # Make a POST request
# response = requests.post(endpoint, json=data)

# # Check the response
# print(response.json())

# %%

import requests
import uuid

# Generate a UID
uid = str(uuid.uuid4())

#%%

# Define the API endpoint
endpoint = "http://localhost:5000/ask"

# The query you want to ask
data = {
    "uid": uid,
    "query": "Yes you do"
}

# Make a POST request
response = requests.post(endpoint, json=data)

# Check the response
print(response.json())
print(len(response.json()['chat_history']))

#%%

print(response.json()['chat_history'][-1])

# %%
