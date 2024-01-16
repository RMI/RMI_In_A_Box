#%%

from pydantic import BaseModel
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAI
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from typing import List
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts.prompt import PromptTemplate
from operator import itemgetter
from langchain.schema import format_document
from langchain_core.messages import AIMessage, HumanMessage, get_buffer_string
from langchain_core.runnables import RunnableParallel
import logging


#%%

# Load environment variables
env_path = '/Users/hugh/Library/CloudStorage/OneDrive-RMI/Documents/RMI/envs/azure_storage.env'
load_dotenv(dotenv_path=env_path)
openai_api_key = os.getenv('OPENAI_API_KEY')

# Initialize vector store
persist_directory = "./data"
vectordb = Chroma(persist_directory=persist_directory, embedding_function=OpenAIEmbeddings(openai_api_key=openai_api_key))
print("Vector store initialized.")

# # Use a dictionary as a mock in-memory database
# sessions = {}

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
                | (lambda x: print("Standalone question prompt:", x) or x)
                | self.llm
                | (lambda x: print("after llm:", x) or x)
                | StrOutputParser()
                | (lambda x: print("after outparser:", x) or x),
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
            final_chain = loaded_memory | (lambda x: print("after loaded memory:", x) or x) | standalone_question| (lambda x: print("after standalone:", x) or x) | retrieved_documents| (lambda x: print("after retrieved:", x) or x) | answer
            self.memories[uid] = memory, final_chain
        return self.memories[uid]

# Initialize LLM and retriever
llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo', openai_api_key=openai_api_key)
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

def ask(request: AskRequest):
    uid = request.uid
    query = request.query

    memory, chain = memory_manager.get_memory_for_user(uid)
    memory.load_memory_variables({})

    # Ask the question and get response
    try:
        input = {"question": query}
        result = chain.invoke(input)
    except Exception as e:
        print(f"Error while asking question: {e}")
    answer = result["answer"].content
    #sources = [{"source": doc.metadata["source"], "page": doc.metadata["page"]+1} for doc in result["source_documents"]]
    sources = [Source(source=doc.metadata["source"].split('/')[-1], page=doc.metadata["page"]+1) for doc in result["docs"]]

    memory.save_context(input, {"answer": answer})

    return AskResponse(answer=answer, sources=sources)

#%%

ask(AskRequest(uid="65", query="rephrase your previous answer"))


# %%

# for i in range(1000):
#     ask(AskRequest(uid="5", query="Explain emissions from dam building"))

# %%
