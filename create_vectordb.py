#%%

import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import Docx2txtLoader
from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
import tempfile
from dotenv import load_dotenv
import concurrent.futures
import zipfile

load_dotenv('/Users/hugh/Library/CloudStorage/OneDrive-RMI/Documents/RMI/envs/azure_storage.env')

# # Get the connection string from an environment variable
# connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

# # Create a blob client using the storage account's connection string
# blob_service_client = BlobServiceClient.from_connection_string(connect_str)

# # Function to download and process a blob (file)
# def download_and_process_blob(blob):
#     print(f"Processing blob: {blob.name}")
#     documents = []
    
#     # Extract the original file name from the blob name
#     original_file_name = blob.name.split('/')[-1]

#     blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob.name)
#     data = blob_client.download_blob().readall()

#     # Save blob data to a temporary file
#     with tempfile.NamedTemporaryFile(delete=False, suffix=blob.name) as temp_file:
#         temp_file.write(data)
#         temp_file_path = temp_file.name

#         # Depending on the file type, process the data using the temp file path
#         if blob.name.endswith(".pdf"):
#             loader = PyPDFLoader(temp_file_path)
#             documents.extend(loader.load())
#         elif blob.name.endswith('.docx') or blob.name.endswith('.doc'):
#             loader = Docx2txtLoader(temp_file_path)
#             documents.extend(loader.load())
#         elif blob.name.endswith('.txt'):
#             loader = TextLoader(temp_file_path)
#             documents.extend(loader.load())

#         # # Load the documents and set metadata
#         # loaded_documents = loader.load()
#         # for doc in loaded_documents:
#         #     doc.metadata["name"] = original_file_name
#         # documents.extend(loaded_documents)
    
#     return documents

# # Specify the container name
# container_name = "chatbot-training-docs"
# container_client = blob_service_client.get_container_client(container_name)

# # List the blobs in the container
# blobs = list(container_client.list_blobs())
# print(f"Total blobs in container: {len(blobs)}")

# # Download and process blobs in parallel
# documents = []
# with concurrent.futures.ThreadPoolExecutor() as executor:
#     # Map returns results in the order they were started.
#     for blob_documents in executor.map(download_and_process_blob, blobs):
#         documents.extend(blob_documents)

# print(f"Total documents extracted: {len(documents)}")

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

# Path to the directory to be zipped
dir_path = './data'

# Name for the zipped file
zip_filename = "data.zip"

# Function to zip a directory
def zipdir(path, ziph):
    # Calculate the length of the path prefix to be removed from archive names
    path_prefix_len = len(os.path.dirname(path)) + 1

    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            # Calculate archive name by removing the path prefix
            archive_name = file_path[path_prefix_len:]
            ziph.write(file_path, archive_name)

with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipdir(dir_path, zipf)

#%%
    
# Debugging: Print sample metadata from documents
print("\nSample document metadata:")
for i, doc in enumerate(documents[:5]):  # Adjust the range as needed
    print(f"Document {i}:")
    print(doc.metadata)

print(f"Total document chunks after splitting: {len(documents)}")

#%%

# Specify the destination container name
dest_container_name = "vectordb"

# Define a blob name for the serialized data
blob_name = zip_filename

# Get the connection string from an environment variable
connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

# Create a blob client using the storage account's connection string
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

# Get a blob client for uploading
dest_blob_client = blob_service_client.get_blob_client(container=dest_container_name, blob=blob_name)

# Upload the zipped file
with open(zip_filename, "rb") as data:
    dest_blob_client.upload_blob(data, overwrite=True)

# # Remove the zip file after uploading
# os.remove(zip_filename)

# %%
