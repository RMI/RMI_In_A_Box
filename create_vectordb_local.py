#%%

import os
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import Docx2txtLoader
from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from dotenv import load_dotenv

load_dotenv('/Users/hugh/Library/CloudStorage/OneDrive-RMI/Documents/RMI/envs/azure_storage.env')

doc_folder_path = 'report_pdfs/'

documents = []
# Create a list of Documents from all of our files stored in doc_folder_path
for file in os.listdir(doc_folder_path):
    if file.endswith(".pdf"):
        pdf_path = doc_folder_path  + file
        loader = PyPDFLoader(pdf_path)
        documents.extend(loader.load())
    elif file.endswith('.docx') or file.endswith('.doc'):
        doc_path = doc_folder_path + file
        loader = Docx2txtLoader(doc_path)
        documents.extend(loader.load())
    elif file.endswith('.txt'):
        text_path = doc_folder_path + file
        loader = TextLoader(text_path)
        documents.extend(loader.load())

# Split the documents into smaller chunks
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=10)
documents = text_splitter.split_documents(documents)

print(f"Total document chunks after splitting: {len(documents)}")

# Get the OpenAI API key from an environment variable
openai_api_key = os.getenv('OPENAI_API_KEY')

# Convert the document chunks to embedding and save them to the vector store
vectordb = Chroma.from_documents(documents, embedding=OpenAIEmbeddings(), persist_directory="./data")
vectordb.persist()

# %%
