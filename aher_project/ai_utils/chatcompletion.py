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
        self._original_messages = messages
        self.flowdata = {}
        self.response = ""
        
        fallback_system_message = """
            You are a helpful assistant specialized in historical locations and heritage. Follow user requests carefully, consisely and provide clear, factual responses using the data provided.
        """
        
        default_system_prompt = getattr(settings, 'DEFAULT_SYSTEM_PROMPT', fallback_system_message)
        self._original_messages = [msg for msg in self._original_messages if msg.get('role') != 'system']
        self._original_messages.insert(0, {"role": "system", "content": default_system_prompt})
        
        self.messages = self.get_summarise_message_history()

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

    def response(self) -> str:
        """Return the response message from the chat flow."""
        return self.response
    
    def set_response(self, response: str):
        """Set the response message in the chat flow."""
        self.response = response

    def llm_summarize_messages(self):
        """Summarize the messages in the chat flow using the LLM."""    
        chat_provider = get_chat_provider()
        summarize_prompt = """
                        Summarize the conversation history in a concise yet informative manner.
                        Capture key topics, user intent, and any relevant context to ensure continuity. 
                        Identify and highlight any locations, named areas, or places mentioned in the conversation, ensuring they are preserved in the summary. 
                        Exclude unnecessary details but retain important facts, decisions, and unresolved questions. 
                        The summary should be clear and structured to be passed along with additional retrieval-augmented context and the latest user message for the next response.
                        """ 
        system_message = {"role": "system", "content": "You are a summarizing tool that will help to summarize a conversation history in a concise yet informative manner."}
        
        #print(f"ORIGINAL_MESSAGES: {self._original_messages}")
        
        pre_query_messages = [msg for msg in self._original_messages if msg["role"] in ["user", "assistant"]]

        # if the pre_query_messages contains more that just the last user message, remove the last user message
        if len(pre_query_messages) > 1:
            pre_query_messages.pop()


        #print(f"PRE_QUERY_MESSAGES: {pre_query_messages}")
        # add system message
        pre_query_messages.insert(0, system_message)
        # add summarize prompt
        pre_query_messages.append({"role": "user", "content": summarize_prompt})
        #print(f"PRE_QUERY_MESSAGES_WITH_QUERY: {pre_query_messages}")
        response = chat_provider.complete_chat(pre_query_messages)
        #print(f"SUMMARY: {response.content}")
        summary = response.content
        return summary
    
    def get_summarise_message_history(self):
        """Re-create the message history so that the messages between the system and the last user message are summarized."""

        # if messages only contain the system message and the last user message, return the original messages
        if len(self._original_messages) <= 2:
            return self._original_messages


        summary_message = self.llm_summarize_messages()
        summary_message_history = []
        # add the system message from self.messages
        summary_message_history.append(self._original_messages[0])
        # add the summarized message
        summary_message_history.append({"role": "assistant", "content": summary_message})
        # add the last user message
        summary_message_history.append(self._original_messages[-1])
        return summary_message_history
        
    

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

    def execute(self, messages: ChatFlowMessages) -> List[Dict[str, Any]]:
        """Execute the chat flow through all registered nodes."""
        for node in self.nodes:
            messages = node.process(messages)

        # print response
        print(f"RESPONSE: {messages.response}")

        if messages.response:
            return messages.response
        else:
            return "No response generated."

    def format_output(self, response: str) -> Dict[str, Any]:
        """Format the output response to fit the required structure."""
        return {"response": response}

def get_chat_provider(provider: Optional[str] = None) -> ChatProvider:
    """Factory function to get a chat provider instance."""
    provider = provider or getattr(settings, 'DEFAULT_CHAT_PROVIDER', 'ollama')
    return ChatProvider(provider)


"""
import json
from arches.app.utils.betterJSONSerializer import JSONSerializer
from aher_project.ai_utils.chatcompletion import get_chat_provider, ChatFlow, ChatFlowMessages
from aher_project.ai_utils.nodes.identify_locations import LocationExtractNode, LocationFilterNode
from aher_project.ai_utils.nodes.semantic_search import SemanticSearchNode, SemanticSearchSummarizeNode,SemanticSearchResponseNode
msg = [{"role": "system", "content": "Yo"}, {"role": "user", "content": "I'm intersted in the history of Camden. Also what pubs are there in Cirencester?"}]
chat_provider = get_chat_provider()
chat_flow = ChatFlow()
chat_flow.register_node(LocationExtractNode())
chat_flow.register_node(LocationFilterNode())
chat_flow.register_node(SemanticSearchNode())
chat_flow.register_node(SemanticSearchSummarizeNode())
chat_flow.register_node(SemanticSearchResponseNode())
chat_messages = ChatFlowMessages(msg)
updated_messages = chat_flow.execute(chat_messages)
print(f"OUTPUT: {JSONSerializer().serialize(updated_messages, indent=2)}")
print("_"*50)


"""