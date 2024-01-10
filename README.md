# RMI_In_A_Box

This repo is an experiment to generate QA chatbot for RMI reports and documents. It is adapted from [an open source project](https://github.com/smaameri/multi-doc-chatbot#summary) that uses Langchain under the hood.

## Getting Started  

Clone the repository, set up the virtual environment, and install the required packages

git clone https://github.com/rosewangrmi/RMI_In_A_Box

cd RMI_In_A_Box

python3 -m venv .venv

. .venv/bin/activate

pip install -r requirements.txt


## Store your OpenAI API key

Create a .env file, and save the openai api key

OPENAI_API_KEY =


## Provide the path to documents in the .env file

DOC_FOLDER_PATH =

## Generate vectordb
python3 create_vectordb.py

## Start chatting
python3 qa.py

## New Dockerized Version

Download the repo, navigate to it, and run

docker build -t box .

docker run -p 5000:5000 -e AZURE_STORAGE_CONNECTION_STRING='string_here' -e OPENAI_API_KEY='key_here' box

Then use something like a jupyter notebook to ask questions, using the code structure in test_api.py

## API is now running on Azure

Use code like the example in test_api.py, accessible at https://rmi-in-a-box.politemushroom-551f150f.westus2.azurecontainerapps.io/. If you set your uid only once and continue to use the same one, it should remember your conversation history. Just put your question in, run the cell, retype a new question, run the cell again, etc.
