from langchain_mistralai.chat_models import ChatMistralAI
from app.core.config import settings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.retrievers import BaseRetriever

# Initialize the chat model
chat_model = ChatMistralAI(
    model_name="mistral-large-latest",
    api_key=settings.MISTRAL_API_KEY,
    max_retries=3,
)

# Define the prompt template for the question-answering chain
prompt = PromptTemplate.from_template(
    """Use Only the following context to answer the question. If you don't know the answer, just say "I don't know". Never make up an answer.
    Context: {context}
    Question: {question}
    """
)

# Define the output parser to format the response
output_parser = StrOutputParser()

def format_docs(docs):
    """
    Formats the retrieved documents into a string for the prompt.
    
    Args:
        docs (list): List of documents retrieved by the retriever.
    
    Returns:
        str: Formatted string of documents.
    """
    return "\n\n".join([doc.page_content for doc in docs])


async def answer_question(question: str, retriever: BaseRetriever) -> str:
    """
    Answers a question using the question-answering chain.
    
    Args:
        question (str): The question to be answered.
    
    Returns:
        str: The answer to the question.
    """

    # Create the runnable for the question-answering chain
    qa_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | chat_model
        | output_parser
    )
    # Run the QA chain with the provided question
    response = await qa_chain.ainvoke(input=question)
    response = response.content if hasattr(response, 'content') else response

    return response