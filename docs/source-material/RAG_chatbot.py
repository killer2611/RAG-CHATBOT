import os
import nest_asyncio
import pandas as pd  

#Environment Setup (Disable caching and timeouts)
os.environ["DEEPEVAL_DISABLE_TIMEOUTS"] = "1"
os.environ["DEEPEVAL_DISABLE_CACHE"] = "YES"
nest_asyncio.apply()

from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, ContextualPrecisionMetric, ContextualRecallMetric
from deepeval.test_case import LLMTestCase
from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
from deepeval.models import GeminiModel
from deepeval.evaluate.configs import CacheConfig
from deepeval.evaluate import AsyncConfig, ErrorConfig
from deepeval.evaluate.configs import CacheConfig

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import PyPDFLoader
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_classic.chains import create_history_aware_retriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.storage import InMemoryStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableWithMessageHistory

golden_qa_pairs = ['Add your golden qa pair for evaluation']

judge_model = GeminiModel( model="gemini-3.6-flash",
    api_key="Your Gemini API Key",
    temperature=0
)
llm = ChatGroq(model="Qwen3.6",api_key='Your Groq api key here', temperature=0.1)
session = {}

def get_session_history(session_code):
    if session_code not in session:
        session[session_code] = ChatMessageHistory()
    return session[session_code]

loader = PyPDFLoader('Your file path')
pdf = loader.load()
embed = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=40)

vector_store = Chroma(embedding_function=embed)
memory = InMemoryStore()

base_parent_retriever = ParentDocumentRetriever(
    vectorstore=vector_store,
    parent_splitter=parent_splitter,
    child_splitter=child_splitter,
    docstore=memory,
    search_kwargs={"k": 10}
)
base_parent_retriever.add_documents(pdf)

reranker_model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")
compressor = CrossEncoderReranker(model=reranker_model, top_n=3)
retriever = ContextualCompressionRetriever(
    base_compressor=compressor, 
    base_retriever=base_parent_retriever
)
contextualize_prompt = ChatPromptTemplate.from_messages([
    ("system", "Given the chat history and the latest user question, rewrite the latest question into a standalone question.\n\nDo not answer it."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a factual assistant. Answer the question ONLY using the provided context below.

If the answer cannot be fully deduced from the context, state: "I do not have enough information to answer this based on the provided documents."

Do not assume or extrapolate.

Context:
{context}"""),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}")
])

document_chain = create_stuff_documents_chain(llm, qa_prompt)
history_retriver = create_history_aware_retriever(llm, retriever, contextualize_prompt)
main_chain = create_retrieval_chain(history_retriver, document_chain)

chatbot = RunnableWithMessageHistory(
    main_chain,
    get_session_history=get_session_history,
    input_messages_key="input",
    output_messages_key="answer",
    history_messages_key="chat_history"
)
config = {"configurable": {"session_id": "user_session_abc"}}

def create_test_case(question, answer):
    result = chatbot.invoke({'input': question}, config=config)
    docs = retriever.invoke(question)
    return LLMTestCase(
        input=question,
        expected_output=answer,
        actual_output=result['answer'],
        retrieval_context=[doc.page_content for doc in docs]
    )

def evaluate_chatbot():
    metrics = [
    FaithfulnessMetric(threshold=0.7, model=judge_model),
    AnswerRelevancyMetric(threshold=0.7, model=judge_model),
    ContextualPrecisionMetric(threshold=0.7, model=judge_model),
    ContextualRecallMetric(threshold=0.7, model=judge_model),]

    test_case = [create_test_case(q, a) for q, a in golden_qa_pairs]
    async_config = AsyncConfig(run_async=False)
    error_config = ErrorConfig(ignore_errors=True)
    results = evaluate(
    test_case,
    metrics,
    cache_config=CacheConfig(write_cache=False, use_cache=False),
    async_config=async_config,
    error_config=error_config)
    records = []
    for result in results.test_results:
        print(f"\nQuestion: {result.input}")
    
        # Initialize the row structure for CSV
        row = {
        "Question": result.input,
        "Actual Output": result.actual_output,
        "Expected Output": result.expected_output,
        "Success": result.success,
        }
        for metric_data in result.metrics_data:
            print(f"  {metric_data.name}: score={metric_data.score:.2f}  "
                  f"passed={metric_data.success}  reason={metric_data.reason}")
        records.append(row)
    df_eval = pd.DataFrame(records)
    df_eval.to_csv("rag_final_eval_report.csv", index=False)
def chatbot_run():
     while True:
          user_input=input("You: ")
          if user_input=='bye' or user_input=='end':
               break
          else:
               result=chatbot.invoke({'input':user_input},config=config)
               print(f"AI: {result['answer']}")
