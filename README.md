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
