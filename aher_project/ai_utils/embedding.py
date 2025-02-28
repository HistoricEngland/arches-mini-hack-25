from typing import List, Optional
from langchain_core.embeddings import Embeddings
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from arches.app.models.system_settings import settings

class EmbeddingProvider:
    """Abstraction for different embedding providers using LangChain."""
    
    def __init__(self, provider: str = "azure"):
        self.provider = provider
        self._client = self._initialize_client()

    def _initialize_client(self) -> Embeddings:
        """Initialize the appropriate embedding client based on provider."""
        if self.provider == "azure":
            return AzureOpenAIEmbeddings(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                model=settings.AZURE_OPENAI_EMBEDDING_MODEL,
            )
        elif self.provider == "ollama":
            return OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_EMBEDDING_MODEL,
            )
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        return self._client.embed_query(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch."""
        return self._client.embed_documents(texts)

    @property
    def dimension(self) -> int:
        """Return the dimension of the embeddings."""
        if self.provider == "azure":
            return 1536  # Azure OpenAI text-embedding-3-small dimension
        elif self.provider == "ollama":
            return 1536
        return 0

def get_embedder(provider: Optional[str] = None) -> EmbeddingProvider:
    """Factory function to get an embedding provider instance."""
    provider = provider or getattr(settings, 'DEFAULT_EMBEDDING_PROVIDER', 'ollama')
    return EmbeddingProvider(provider)