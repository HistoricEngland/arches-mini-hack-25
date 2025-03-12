from typing import List, Dict, Any
import json
from django.db.models.expressions import RawSQL
from pgvector.django import CosineDistance
from aher_project.ai_utils.chatcompletion import ChatFlowNode, ChatFlowMessages, get_chat_provider
from aher_project.models.arches_embeddings import TileEmbeddingDocument
from aher_project.ai_utils.embedding import get_embedder

class SemanticSearchNode(ChatFlowNode):
    """
    Node to perform semantic search on TileEmbeddingDocuments.
    If location filter data is present in flowdata, it will restrict the search to resources within that area.
    """
    
    def __init__(self):
        super().__init__("Semantic Search Node")
    

    def process(self, messages: ChatFlowMessages) -> ChatFlowMessages:
        """Process the messages and perform semantic search."""
        # Get the last user message for embedding
        user_messages = [msg["content"] for msg in messages.messages if msg["role"] in ["user", "assistant"]]
        if not user_messages:
            return messages
        
        # the emedding search needs all the messages to be concatenated
        query_text = " ## ".join(user_messages)
        
        embedder = get_embedder()
        query_embedding = embedder.embed_text(query_text)
        
        # Base query
        query = TileEmbeddingDocument.objects.all()
        
        # Apply location filter if present to only consider resources within that area
        try:
            location_filter = messages.get_flowdata("location_filter_node")
            if location_filter:
                spatial_filter = f"""
                    SELECT resourceinstanceid
                    FROM public.geojson_geometries
                    {location_filter}
                """
                # Filter based on the join
                query = query.filter(
                    resourceinstance_id__in=RawSQL(spatial_filter, [])
                )
        except KeyError:
            pass  # No location filter present, continue with base query
        
        #annotate the query with the cosine distance
        query = query.annotate(
            distance=CosineDistance('embedding', query_embedding)
        )

        # Perform semantic search and get the top 20 tile embeddings
        results = query.order_by(CosineDistance('embedding', query_embedding))[:5]  # Limit to top 5 results

        # print the displaname and distance
        for result in results:
            print(f"resource: {result.resourceinstance.displayname()} distance: {result.distance}")

        # if the distance is less than 0.3, then we can consider it as a match
        results = [result for result in results if result.distance < 0.5]
        
        if not results:
            print("+++++++++++++++++ No semantic search results found.")
            messages.set_response(" No relevent results have been found in the database. Please try again.")
            return messages

        # Aggregate the results by resource instance
        results = TileEmbeddingDocument.aggregate_by_resource(results)
        #print(f"semantic results: {results}")
        # Add the results to the flowdata
        messages.add_flowdata("semantic_search_results", results)
        
        
        return messages
    
class SemanticSearchSummarizeNode(ChatFlowNode):
    """
    Node to summarize the semantic search results relevent to the message history.
    """
    
    def __init__(self):
        super().__init__("Semantic Search Summarize Node")
    
    

    def llm_summarize_messages(self, rag_results: List[Dict[str, Any]]) -> str:
        """Summarize the messages using the LLM."""
        """
        {
            'order': 0.38,
            'document': f"# Title: Excavation 1\n\n## Summary Description\nThis is the display description of the resource}\n\n## Content\n",
            'document_source_url': "http://localhost:8002/report/12323-123-123-123"
        }
        """

        # put the rag_results into a multi-line string with ewach doc seperated by 3 line breaks
        formatted_docs = "\n\n\n".join([f"- Document: {doc['document']}\n   - Document Source: {doc['document_source_url']}" for doc in rag_results])
        
        return formatted_docs

        semenatic_search_prompt = f"""
            Rewrite the following collection of documents, which use JSON, into a readable format using the structure below. 
            For each document, captures the main points, key insights, and important details.
            Ensure that the source url is included. 
            Preserve relevant facts, figures, and named entities while removing unnecessary details. 
            The document should be clear and well-organized to be used later for responding to user queries.

            OUTPUT FORMAT:

            - Title: [Document Title]
            - Document: [The content of the document rewritten in a readable format]
            - Source: [put the document_source_url here]


            DOCUMENTS:

            {formatted_docs}
        """
        print("-"*50)
        print(f"semantic search prompt: {semenatic_search_prompt}")

        chat_provider = get_chat_provider()
        messages = [
            {"role": "system", "content": "You are a document rewrite tool that will create a readable format for a collection of json documents."},
            {"role": "user", "content": semenatic_search_prompt}
        ]
        response = chat_provider.complete_chat(messages)
        summary = response.content


        print("-"*50)
        print(f"semantic search summary: {summary}")
        return summary
    
    def process(self, messages: ChatFlowMessages) -> ChatFlowMessages:
        """Process the messages and summarize the semantic search results."""
        # Get the semantic search results
        try:
            semantic_search_results = messages.get_flowdata("semantic_search_results")
        except KeyError:
            print("+++++++++++++++++ No semantic_search_node results found in the flowdata.")
            return messages
        
        # Summarize the results        
        summary = self.llm_summarize_messages(semantic_search_results)
        
        # Add the summary to the flowdata
        messages.add_flowdata("semantic_search_summary", summary)
        
        return messages

class SemanticSearchResponseNode(ChatFlowNode):
    """
    Node to generate a response using semantic search results and chat history
    """
    
    def __init__(self):
        super().__init__("Semantic Search Response Node")
    
    def process(self, messages: ChatFlowMessages) -> ChatFlowMessages:
        """Process the messages and generate a response using semantic search results."""
        try:
            semantic_search_results = messages.get_flowdata("semantic_search_summary")
        except KeyError:
            print("++++++++++++++++++++++ No semantic_search_summary found in the flowdata.")
            return messages
            
        # Get the last user message
        user_messages = [msg for msg in messages.messages if msg["role"] == "user"]
        if not user_messages:
            return messages
        last_user_message = user_messages[-1]["content"]
        
        # Create prompt using semantic search results
        context = json.dumps(semantic_search_results, indent=2)
        prompt = f"""
                    Use the following context data from your database, along with the chat history, to answer the user's question.
                    - Do NOT use any information outside of the context provided.
                    - If you don't have enough information to answer the question, you can say so.
                    - Do not mention you are an AI or provide any other information about the system.
                    - Do not provide any personal opinions or assumptions.
                    - Simply answer the question based on the information provided.
                    - If the answer is not found in the context, answer as best you can with the data you've been provided without lhying or making up informaiton.
                    - Do not refer the context data provided, answer as if it was coming from your own knowledge.
                    
                    You MUST ALWAYS add sources for the information you provide.
                    - Add all source urls for the documents that you used to answer the question at the bottom of the response in a bulleted list with a reference number.
                    - The url should be clickable in an HTML format, e.g.,<a target="_blank" href="https://www.example.com">[ref number] the document title </a>
                    - You MUST add the reference number for the source in the response where it was used to generate content.

                    Context Data:
                    {context}

                    User's question: {last_user_message}
        """

        # print prompt
        print("-"*50)
        print(f"semantic search prompt: {prompt}")


        chat_provider = get_chat_provider()
        
        message_history_summary_excluding_latest_and_system = messages.messages[1:-1]
        # append the prompt to the message history
        message_history_summary_excluding_latest_and_system.append({"role": "user", "content": prompt})

        response = chat_provider.complete_chat(message_history_summary_excluding_latest_and_system,)
        
        # Add the response to the messages
        messages.messages.append({
            "role": "assistant",
            "content": response.content
        })


        # set message response if this may be a suitable reply
        messages.set_response(response.content)

        print("-"*50)
        print(f"semantic search response: {response.content}")
        
        return messages