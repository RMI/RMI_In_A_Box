# RMI_In_A_Box

This repo is an experiment to generate QA chatbot for RMI reports and documents. It is adapted from [an open source project](https://github.com/smaameri/multi-doc-chatbot#summary) that uses Langchain under the hood.

Questions can be asked here:
https://box-frontend.politemushroom-551f150f.westus2.azurecontainerapps.io

## If you want to run it locally

Clone the repository, set up the virtual environment, and install the required packages

git clone https://github.com/rosewangrmi/RMI_In_A_Box

cd RMI_In_A_Box

Create a .env file, and save your openai api key

OPENAI_API_KEY =

pip install -r requirements.txt
pip install doc2text docx2txt

Open create_vectordb_local.py and change the load_dotenv path on line 12 to where you saved your .env file. Change line 14 doc_folder_path to where you have the pdf source documents saved.

Run create_vectordb_local.py. You might need to alter the persist_directory path on line 42.

Open qa_local.py, change the .env file path on line 32, and run it. Make sure the persist_directory path on line 37 matches the previous one from create_vectordb_local.py line 42. Questions are asked by running line 152.
