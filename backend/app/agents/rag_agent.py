"""
LangGraph-based RAG Agent for AML Policy FAQ Bot.
"""

from typing import AsyncGenerator
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from app.core.config import init_settings
from app.schemas import SourceDocument, StreamChunk


class RAGState(MessagesState):
    """Extended MessagesState for RAG pipeline."""
    question: str
    context: str
    sources: list[SourceDocument]
    escalate: bool


def get_llm() -> ChatNVIDIA:
    """Get NVIDIA LLM instance."""
    settings = init_settings()
    if not settings.NVIDIA_API_KEY:
        raise ValueError("NVIDIA_API_KEY is required")
    return ChatNVIDIA(
        model=settings.NVIDIA_MODEL_NAME,
        api_key=settings.NVIDIA_API_KEY.get_secret_value(),
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )


SYSTEM_PROMPT = """You are an expert AML (Anti-Money Laundering) compliance assistant. 
Answer questions based ONLY on the provided policy documents.

RULES:
1. Base your answer ONLY on the provided context.
2. If not found, say "I don't have this information. Please escalate to a compliance reviewer."
3. Cite specific policy sections when possible.
4. For high-risk scenarios, recommend escalation.

CONTEXT:
{context}
"""


class RAGAgent:
    """RAG Agent using LangGraph."""
    
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.llm = get_llm()
        self._build_graph()
    
    def _build_graph(self):
        graph = StateGraph(RAGState)
        graph.add_node("retrieve", self._retrieve)
        graph.add_node("generate", self._generate)
        graph.add_edge(START, "retrieve")
        graph.add_edge("retrieve", "generate")
        graph.add_edge("generate", END)
        self.graph = graph.compile()
    
    async def _retrieve(self, state: RAGState) -> dict:
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 6})
        docs = await retriever.ainvoke(state["question"])
        
        context_parts = []
        sources = []
        
        for i, doc in enumerate(docs):
            context_parts.append(f"[Doc {i+1}]\n{doc.page_content}")
            sources.append(SourceDocument(content=doc.page_content[:500], metadata=doc.metadata))
        
        return {
            "context": "\n\n".join(context_parts),
            "sources": sources,
            "escalate": len(docs) == 0
        }
    
    async def _generate(self, state: RAGState) -> dict:
        if state.get("escalate"):
            return {"messages": [AIMessage(content="No relevant information found. Please escalate.")]}
        
        response = await self.llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT.format(context=state["context"])),
            HumanMessage(content=state["question"])
        ])
        return {"messages": [response]}
    
    async def query(self, question: str, **kwargs) -> dict:
        result = await self.graph.ainvoke({
            "messages": [HumanMessage(content=question)],
            "question": question,
            "context": "",
            "sources": [],
            "escalate": False
        })
        
        answer = next((m.content for m in reversed(result["messages"]) if isinstance(m, AIMessage)), "")
        return {"answer": answer, "sources": result["sources"], "escalate": result["escalate"]}
    
    async def stream_query(self, question: str, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        initial_state = {"messages": [HumanMessage(content=question)], "question": question, "context": "", "sources": [], "escalate": False}
        
        retrieve_result = await self._retrieve(initial_state)
        initial_state.update(retrieve_result)
        
        if initial_state["escalate"]:
            yield StreamChunk(type="token", content="No relevant information found. Please escalate.")
            yield StreamChunk(type="done", content="")
            return
        
        # Stream LLM tokens only
        async for chunk, _ in self.graph.astream(initial_state, stream_mode="messages"):
            if hasattr(chunk, 'content') and chunk.content:
                yield StreamChunk(type="token", content=chunk.content)
        
        yield StreamChunk(type="done", content="")
