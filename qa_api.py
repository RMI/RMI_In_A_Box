#%%

from flask import Flask, request, jsonify
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from dotenv import load_dotenv
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

app = Flask(__name__)

load_dotenv('.env')

persist_directory = "./data"
embedding = OpenAIEmbeddings()
vectordb = Chroma(
    persist_directory=persist_directory,
    embedding_function=embedding
)

# create our Q&A chain
num_docs = 6
pdf_qa = ConversationalRetrievalChain.from_llm(
    ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo'),
    retriever=vectordb.as_retriever(search_kwargs={'k': num_docs}),
    return_source_documents=True,
    verbose=False
)

chat_history = []


@app.route('/ask', methods=['POST'])
def ask():
    query = request.json.get("query")
    if not query:
        return jsonify({"error": "Query not provided"}), 400

    result = pdf_qa({"question": query, "chat_history": chat_history})
    
    answer = result["answer"]
    sources = [{"source": doc.metadata["source"], "page": doc.metadata["page"]+1} for doc in result["source_documents"]]

    chat_history.append((query, answer))

    return jsonify({
        "answer": answer,
        "sources": sources
    })


if __name__ == '__main__':
    app.run(debug=True)