from langchain_mistralai.embeddings import MistralAIEmbeddings
from app.core.config import settings

mistral_embedder = MistralAIEmbeddings(
    model="mistral-embed",
    api_key=settings.MISTRAL_API_KEY,
)
