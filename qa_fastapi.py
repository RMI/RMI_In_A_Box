from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from azure.storage.blob import BlobServiceClient
import zipfile
from fastapi.responses import RedirectResponse
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from typing import List
from azure.keyvault.secrets import SecretClient
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from typing import List
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
)
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts.prompt import PromptTemplate
from operator import itemgetter
from langchain.schema import format_document
from langchain_core.messages import get_buffer_string

# Initialize FastAPI
app = FastAPI()

try:
    # Create a blob client using the storage account's connection string
    #blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    # Create a BlobServiceClient object using the DefaultAzureCredential
    managed_identity_client_id = os.getenv("MANAGED_IDENTITY_CLIENT_ID")
    credential = DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id)
    #credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url="https://rmiinbox.blob.core.windows.net", credential=credential)
    #blob_service_client = BlobServiceClient(account_url="rmibox.blob.core.windows.net", credential=DefaultAzureCredential())

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
print("Unzipping completed.")

# List files in the data directory
data_dir = './data'
print(f"Contents of {data_dir}:")
for filename in os.listdir(data_dir):
    print(filename)

# Create vector store
#from dotenv import load_dotenv
#load_dotenv('/Users/hugh/Library/CloudStorage/OneDrive-RMI/Documents/RMI/envs/azure_storage.env')
#embedding = OpenAIEmbeddings(openai_api_key=os.getenv('OPENAI_API_KEY'))
try:
    key_vault_uri = "https://rmibox.vault.azure.net/"
    client = SecretClient(vault_url=key_vault_uri, credential=credential)
    secret_name = "openai-api"
    retrieved_secret = client.get_secret(secret_name)
    print(f"Retrieved secret: {retrieved_secret.value}")
    embedding = OpenAIEmbeddings(openai_api_key=retrieved_secret.value)
except Exception as e:
    print(f"Error retrieving secret: {e}")
persist_directory = "./data/data"
vectordb = Chroma(
    persist_directory=persist_directory,
    embedding_function=embedding
)
print("Vector store initialized.")

class MemoryManager:
    def __init__(self, llm, retriever, max_token_limit=4000):
        self.memories = {}
        self.llm = llm
        self.retriever = retriever
        self.max_token_limit = max_token_limit

    def get_memory_for_user(self, uid):
        if uid not in self.memories:
            memory = ConversationSummaryBufferMemory(return_messages=True, output_key="answer", input_key="question", llm=self.llm, max_token_limit=self.max_token_limit)
            # First we add a step to load memory
            # This adds a "memory" key to the input object
            loaded_memory = RunnablePassthrough.assign(
                chat_history=RunnableLambda(memory.load_memory_variables) | itemgetter("history"),
            )
            # Now we calculate the standalone question
            _template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

                Chat History:
                {chat_history}
                Follow Up Input: {question}
                Standalone question:"""
            CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)
            standalone_question = {
                "standalone_question": {
                    "question": lambda x: x["question"],
                    "chat_history": lambda x: get_buffer_string(x["chat_history"]),
                }
                | CONDENSE_QUESTION_PROMPT
                | self.llm
                | StrOutputParser(),
            }
            # Now we retrieve the documents
            retrieved_documents = {
                "docs": itemgetter("standalone_question") | retriever,
                "question": lambda x: x["standalone_question"],
            }
            # Now we construct the inputs for the final prompt
            DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")
            def _combine_documents(
                docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
            ):
                doc_strings = [format_document(doc, document_prompt) for doc in docs]
                return document_separator.join(doc_strings)
            final_inputs = {
                "context": lambda x: _combine_documents(x["docs"]),
                "question": itemgetter("question"),
            }
            # And finally, we do the part that returns the answers
            template = """Answer the question based only on the following context:
                {context}

                Question: {question}
            """
            ANSWER_PROMPT = ChatPromptTemplate.from_template(template)
            answer = {
                "answer": final_inputs | ANSWER_PROMPT | self.llm,
                "docs": itemgetter("docs"),
            }
            # And now we put it all together!
            final_chain = loaded_memory | standalone_question | retrieved_documents| answer
            self.memories[uid] = memory, final_chain
        return self.memories[uid]

# Initialize LLM and retriever
llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo', openai_api_key=retrieved_secret.value)
num_docs = 5
retriever=vectordb.as_retriever(search_kwargs={'k': num_docs})

# Initialize MemoryManager
memory_manager = MemoryManager(llm=llm, retriever=retriever)

# Pydantic models for request and response
class AskRequest(BaseModel):
    uid: str
    query: str

class Source(BaseModel):
    source: str
    page: int

class AskResponse(BaseModel):
    answer: str
    sources: List[Source]

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

    memory, chain = memory_manager.get_memory_for_user(uid)
    memory.load_memory_variables({})

    # Ask the question and get response
    try:
        input = {"question": query}
        result = chain.invoke(input)
    except Exception as e:
        print(f"Error while asking question: {e}")
        raise HTTPException(status_code=500, detail="Error with Q&A model, try rewording the question or using a new UID")
    answer = result["answer"].content
    #sources = [{"source": doc.metadata["source"], "page": doc.metadata["page"]+1} for doc in result["source_documents"]]
    sources = [Source(source=doc.metadata["source"].split('/')[-1], page=doc.metadata["page"]+1) for doc in result["docs"]]

    memory.save_context(input, {"answer": answer})

    print(f"Response ready to be sent. Sources: {sources}")
    return AskResponse(answer=answer, sources=sources)

# Asynchronous entry point for FastAPI
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)


#%%

# from fastapi import Request
# import json

# # Create an AskRequest object
# request = AskRequest(uid="55", query="Explain downstream oil emissions")

# # Call the endpoint function directly
# response = ask(request)

# print(response.answer)
# print(response.sources)
# print(len(response.sources))

#%%
