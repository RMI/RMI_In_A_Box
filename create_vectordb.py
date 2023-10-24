import os
#from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import Docx2txtLoader
from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
import tempfile

#load_dotenv('.env')

# Get the connection string from an environment variable
connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

# Create a blob client using the storage account's connection string
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

# Specify the container name
container_name = "chatbot-training-docs"

container_client = blob_service_client.get_container_client(container_name)

documents = []

# Loop through each blob in the container
for blob in container_client.list_blobs():
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob.name)
    data = blob_client.download_blob().readall()
    
    # Save blob data to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=blob.name) as temp_file:
        temp_file.write(data)
        temp_file_path = temp_file.name

        # Depending on the file type, process the data using the temp file path
        if blob.name.endswith(".pdf"):
            loader = PyPDFLoader(temp_file_path)
            documents.extend(loader.load())
        elif blob.name.endswith('.docx') or blob.name.endswith('.doc'):
            loader = Docx2txtLoader(temp_file_path)
            documents.extend(loader.load())
        elif blob.name.endswith('.txt'):
            loader = TextLoader(temp_file_path)
            documents.extend(loader.load())

# Split the documents into smaller chunks
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=10)
documents = text_splitter.split_documents(documents)

# Get the OpenAI API key from an environment variable
openai_api_key = os.getenv('OPENAI_API_KEY')

# Convert the document chunks to embedding and save them to the vector store
embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
vectordb = Chroma.from_documents(documents, embedding=embedding, persist_directory="./data")
vectordb.persist()