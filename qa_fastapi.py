from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
import os
from azure.storage.blob import BlobServiceClient
import zipfile
from fastapi.responses import RedirectResponse

app = FastAPI()

try:
    # Get the connection string from an environment variable
    connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
except Exception as e:
    print(f"Error accessing environment variable for Azure: {e}")


try:
    # Create a blob client using the storage account's connection string
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    # Specify the container and blob name
    container_name = "vectordb"
    blob_name = "data.zip"

    # Get a blob client for downloading
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)


    # Download the vectordb and save it locally
    local_path = "./data.zip"
    with open(local_path, "wb") as f:
        data = blob_client.download_blob()
        data.readinto(f)

    file_size = os.path.getsize(local_path)
    print(f"Downloaded file size: {file_size} bytes")

except Exception as e:
    print(f"Error while handling blob: {e}")


# Unzip the downloaded data
with zipfile.ZipFile(local_path, 'r') as zip_ref:
    zip_ref.extractall("./data")

# Create vector store
embedding = OpenAIEmbeddings()
persist_directory = "./data"
vectordb = Chroma(
    persist_directory=persist_directory,
    embedding_function=embedding
)

# create Q&A chain
num_docs = 6
pdf_qa = ConversationalRetrievalChain.from_llm(
    ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo'),
    retriever=vectordb.as_retriever(search_kwargs={'k': num_docs}),
    return_source_documents=True,
    verbose=False
)

#chat_history = []

# Use a dictionary as a mock in-memory database
sessions = {}

# Pydantic models for request and response
class AskRequest(BaseModel):
    uid: str
    query: str

class AskResponse(BaseModel):
    answer: str
    sources: list

# Redirect the default URL to the OpenAPI docs
@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/docs")

# Endpoint for asking a question
@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    uid = request.uid
    query = request.query

    if not query:
        raise HTTPException(status_code=400, detail="Query not provided")

    if not uid:
        raise HTTPException(status_code=400, detail="UID not provided")

    # Create a dictionary entry for the user if it doesn't exist
    if uid not in sessions:
        sessions[uid] = []

    # Get the chat history for the user
    chat_history = sessions[uid]

    # Ask the question and get response
    result = pdf_qa({"question": query, "chat_history": chat_history})
    answer = result["answer"]
    sources = [{"source": doc.metadata["source"], "page": doc.metadata["page"]+1} for doc in result["source_documents"]]

    # Update the chat history
    chat_history.append((query, answer))
    sessions[uid] = chat_history

    return {
        "answer": answer,
        "sources": sources,
    }

# Asynchronous entry point for FastAPI
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)