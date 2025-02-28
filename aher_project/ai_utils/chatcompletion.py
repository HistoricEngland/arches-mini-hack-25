from typing import List, Dict, Any, Optional
from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from arches.app.models.system_settings import settings

class ChatProvider:
    """Abstraction for different chat providers using LangChain."""
    
    def __init__(self, provider: str = "azure"):
        self.provider = provider
        self._client = self._initialize_client()

    def _initialize_client(self):
        """Initialize the appropriate chat client based on provider."""
        if self.provider == "azure":
            return ChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                model=settings.AZURE_OPENAI_CHAT_MODEL,
            )
        elif self.provider == "ollama":
            return ChatOllama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_LANGUAGE_MODEL,
            )
        else:
            raise ValueError(f"Unsupported chat provider: {self.provider}")

    def complete_chat(self, messages: List[Dict[str, Any]]) -> str:
        """Generate chat completion based on the provided messages."""
        return self._client.invoke(messages)

class ChatFlowMessages:
    """Class to manage the chat flow messages."""
    
    def __init__(self, messages: List[Dict[str, Any]]):
        self.messages = messages
        self.flowdata = {}

    def add_message(self, role: str, content: str):
        """Add a new message to the chat flow."""
        self.messages.append({"role": role, "content": content})

    def get_messages(self) -> List[Dict[str, Any]]:
        """Return the messages in the chat flow."""
        return self.messages

    def clear_messages(self):
        """Clear all messages in the chat flow."""
        self.messages = []

    def __str__(self):
        return str(self.messages)
    
    def clear_flowdata(self):
        """Clear the flowdata in the chat flow."""
        self.flowdata = {}

    def get_flowdata(self, key: str) -> Dict[str, Any]:
        """Return the flowdata in the chat flow."""
        return self.flowdata[key]
    
    def add_flowdata(self, key: str, value: Any):
        """Add a new key-value pair to the flowdata."""
        self.flowdata[key] = value

class ChatFlowNode:
    """Base class for chat flow nodes."""
    def __init__(self, name: str):
        self.name = name
        self.flowdata_key = name.lower().replace(" ", "_")

    def process(self, messages: ChatFlowMessages) -> ChatFlowMessages:
        """Process the messages and return the updated list of messages."""
        raise NotImplementedError("Each node must implement the process method.")

class ChatFlow:
    """Manages the flow of chat completion through a series of nodes."""
    
    def __init__(self):
        self.nodes = []

    def register_node(self, node: ChatFlowNode):
        """Register a new node in the chat flow."""
        self.nodes.append(node)

    def execute(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute the chat flow through all registered nodes."""
        for node in self.nodes:
            messages = node.process(messages)
        return messages

    def format_output(self, response: str) -> Dict[str, Any]:
        """Format the output response to fit the required structure."""
        return {"response": response}

def get_chat_provider(provider: Optional[str] = None) -> ChatProvider:
    """Factory function to get a chat provider instance."""
    provider = provider or getattr(settings, 'DEFAULT_CHAT_PROVIDER', 'ollama')
    return ChatProvider(provider)


"""
from aher_project.ai_utils.chatcompletion import get_chat_provider, ChatFlow, ChatFlowMessages
from aher_project.ai_utils.nodes.identify_locations import LocationExtractNode, LocationFilterNode
msg = [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "I'm intersted in the history of Camden. Also what pubs are there in Cirencester?"}]
chat_provider = get_chat_provider()
chat_flow = ChatFlow()
chat_flow.register_node(LocationExtractNode())
chat_flow.register_node(LocationFilterNode())
chat_messages = ChatFlowMessages(msg)
updated_messages = chat_flow.execute(chat_messages)
print(f"messages: {updated_messages}")
print(f"messages: {updated_messages.flowdata}")
print("End")
# response = chat_provider.complete_chat(updated_messages)

"""