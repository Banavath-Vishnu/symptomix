from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
from groq import Groq
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from src.helper import download_hugging_face_embeddings

# 🌐 Flask Setup
app = Flask(__name__)
load_dotenv()

# 🔐 API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")

if not GROQ_API_KEY or not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
    raise EnvironmentError("Missing API keys in .env")

# 🔌 Groq Client
client = Groq(api_key=GROQ_API_KEY)

# 🔍 Embeddings and Pinecone Index
embeddings = download_hugging_face_embeddings()
embedding_dim = 384
index_name = "medicalbot"

pc = Pinecone(api_key=PINECONE_API_KEY)
if index_name not in pc.list_indexes().names():
    print(f"Creating Pinecone index '{index_name}'...")
    pc.create_index(
        name=index_name,
        dimension=embedding_dim,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

docsearch = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embeddings)
retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# 🧠 In-memory Chat Store for Multiple Users
chat_sessions = {}

# 🤖 RAG Response Generator
def generate_answer_with_groq(chat_id: str, user_query: str, context_docs: list) -> str:
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = []

    messages = chat_sessions[chat_id]

    context = "\n\n".join([doc.page_content for doc in context_docs])

    if not messages:
        messages.append({
            "role": "system",
            "content": (
                "You are a helpful, knowledgeable, and professional medical assistant. "
                "Your task is to provide accurate and concise answers to medical questions based on the provided context. "
                "You are created by Banavath Vishnu from IIT Hyderabad and your name is Symptomix Chat AI. "
                "Use the context below to accurately answer the user's medical question. "
                "If the user greets you, respond with a polite greeting first. "
                "If the answer is not available in the context, say that you don’t know instead of making something up. "
                "Keep your response clear, concise, and medically sound."
            )
        })

    messages.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {user_query}"
    })

    completion = client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        messages=messages,
        temperature=0.4,
        max_tokens=512,
        top_p=1,
        stream=False
    )

    if completion and completion.choices and completion.choices[0].message:
        answer = completion.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": answer})
        return answer

    return "I apologize, but I couldn't generate a response at this time."

# 🧠 Helper: Build retrieval query using history
def get_user_history(chat_id: str):
    if chat_id not in chat_sessions:
        return ""
    return " ".join([
        msg["content"] for msg in chat_sessions[chat_id]
        if msg["role"] == "user"
    ])

# 🌐 Routes
@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/get", methods=["POST"])
def chat():
    data = request.json
    if not data:
        return jsonify({"error": "Missing request data"}), 400

    user_input = data.get("msg")
    chat_id = data.get("chat_id")

    if not user_input or not chat_id:
        return jsonify({"error": "Missing chat_id or msg"}), 400

    # Build context from entire chat history for follow-up support
    full_query = get_user_history(chat_id) + " " + user_input

    # 🔍 Retrieve relevant chunks using full context
    docs = retriever.invoke(full_query)

    # 🤖 Generate response
    response = generate_answer_with_groq(chat_id, user_input, docs)

    return jsonify({"response": response})

@app.route("/reset", methods=["POST"])
def reset_chat():
    data = request.json
    chat_id = data.get("chat_id") if data else None

    if chat_id and chat_id in chat_sessions:
        chat_sessions.pop(chat_id)

    return jsonify({"message": "Chat reset."})

# 🚀 Run Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
