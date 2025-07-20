from langchain_core.messages import HumanMessage
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_mistralai.embeddings import MistralAIEmbeddings
from app.core.config import Settings
import asyncio
import time

settings = Settings()
chat = ChatMistralAI(model="mistral-small", api_key=settings.MISTRAL_API_KEY)
messages = [HumanMessage(content="say a brief hello")]
# For async...

async def main():
    for chunk in chat.stream(messages):
        print(chunk.content, end="", flush=True)
        time.sleep(0.1)
    print("\nDone streaming.")

asyncio.run(main())