from django.views.generic import View
from django.http import JsonResponse
import requests
import json
from django.contrib.gis.geos import GEOSGeometry, WKTWriter
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator  # Add this line
from aher_project.ai_utils.chatcompletion import get_chat_provider, ChatFlow

class AIAPIView(View):
    
    def get(self, request):
        response = self.geometry_return("Camden")
        return JsonResponse({"message": response}, status=200)

    def post(self, request):
        return JsonResponse({"message": "This is a blank API view"}, status=200)
    
    def geometry_return (self,name_to_search):
        
        #Featureservice numbers relate to the following datasets:
        # 4 - Ceremonial Counties
        # 5 - Districts, Metropolitan districts, London boroughs, Unitary authorities
        # 6 - Civil parishes and communities
        # 7 - Wards
        # 9 - Counties
        # 11 - Westminster constituencies
        
        featureservice_numbers = [4, 5, 6, 7, 9, 11]

        # Base URL for the ArcGIS REST API for OS Open Boundary Line
        base_url = "https://services.arcgis.com/qHLhLQrcvEnxjtPr/ArcGIS/rest/services/OS_OpenBoundaryLine/FeatureServer/{}/query?where=NAME LIKE '%25" + name_to_search + "%25'&outFields=NAME,DESCRIPTIO,&returnGeometry=true&returnIdsOnly=false&f=geojson"
        
        
        results = []
        for number in featureservice_numbers:
            current_url = base_url.format(number)
            response = requests.get(current_url)
            
            if response.status_code == 200:
                # Parse the JSON response
                data = response.json()

                if len(data["features"]) > 0:
                    for feature in data["features"]:
                        geometry = feature["geometry"]
                        if geometry:
                            geometryGeos = GEOSGeometry(json.dumps(geometry))
                            centroidPoint = geometryGeos.envelope.centroid
                            wkt_writer = WKTWriter()
                            wkt_geometry = wkt_writer.write(centroidPoint).decode('utf-8') 
                            
                            feature_data = {}
                            feature_data["geometry"] = wkt_geometry
                            feature_data["name"]= feature["properties"]["NAME"] 
                            feature_data["description"] = feature["properties"]["DESCRIPTIO"]
                            results.append(feature_data)
            else:
                print(f"Failed to retrieve data: {response.status_code}")
                
        if len(results) == 0:
            return {"return_prompt": "No results found for the area you've asked for.  Please refine your criteria and try again."}
        
        elif len(results) == 1:
            return results
        
        elif len(results) > 1:
            options = []
            
            for result in results:
                options.append(result["name"] + " (" + result["description"] + ")")    
                        
            return {"results": results,
                    "return_prompt": "Multiple results found.  Which of the following areas would you like us to use?  " + ', '.join(options)}
        
@method_decorator(csrf_exempt, name='dispatch')
class ChatAPIView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            messages = data.get("messages", [])
            if not messages:
                return JsonResponse({"error": "No messages provided"}, status=400)
            
            chat_provider = get_chat_provider()
            chat_flow = ChatFlow()
            # Register any custom nodes here
            # chat_flow.register_node(SomeCustomNode())
            

            ######## Nodes that build the whereclause for the TileEmdbeddingDocument lookup
            # Node to identify locations

            # Node to fetch the geometry for the identified locations
            # Node to build the whereclause for the TileEmbeddingDocument lookup

            ###### Node to retrieve the TileEmbeddingDocument from the database
            # Node to embedd the history of the conversation and pgvector query the TileEmbeddingDocument



            ###### Nodes to check and refine the response
            # Node to check if the response is valid - if not, ask for clarification - FINISH
            
            # Node is valid then summarise the response
            # Node add sources to the response
            # Node to format into Markdown

            ############

            updated_messages = chat_flow.execute(messages)
            response = chat_provider.complete_chat(updated_messages)
            formatted_response = chat_flow.format_output(response)
            
            return JsonResponse(formatted_response, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
"""
- Request body structure
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, I need information about Camden."
                },
                {
                    "role": "assistant",
                    "content": "I can help you with information about Camden. What would you like to know?"
                },
                {
                    "role": "user",
                    "content": "What are the boundaries of Camden?"
                }
            ]
        }
        - Response body
        {
            "message": {
                "role": "assistant",
                "content": "Here is information about Camden's boundaries...",
                "timestamp": "2025-02-28T14:30:00Z"
            },
            "status": "success"
        }
"""