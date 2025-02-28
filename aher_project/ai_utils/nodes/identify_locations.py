from typing import List, Dict, Any, Optional
import requests, json
from django.contrib.gis.geos import GEOSGeometry, WKTWriter
from aher_project.ai_utils.chatcompletion import ChatFlowNode, get_chat_provider, ChatFlowMessages

"""
Inspect the messages and ask LLM to provide a list of named places in a json array.

Then call the ArcGIS REST API to get the geometry for each location.

"""
"""
[
    { "request": [
                        {"role": "user", "content": "I am interested in the history of Camden."},
                        {"role": "assistant", "content": "I can help you with information about Camden. What would you like to know?"},
                        {"role": "user", "content": "What are the boundaries of Camden?"},
                        {"role": "spatial", "content": "where ST_Intersects(geometry, ST_GeomFromText('POLYGON((-}}"},
                        {"role": "documents"}

                    ]},
    { "flowdata": {}}
]
"""



class LocationExtractNode(ChatFlowNode):
    """
    Look at the messages and identify any location names that are mentioned.
    """
    def __init__(self):
        super().__init__("Location Extract Node")

    def extract_locations_from_text_using_llm(self, chat_messages: ChatFlowMessages) -> ChatFlowMessages:
        """Using content from the messages, extract the locations that are mentioned."""
        text = ""
        for message in chat_messages.messages:
            if message["role"] in ["user", "assistant"]:
                text += message["content"] + " | "

        chat_provider = get_chat_provider()

        prompt = f"""
        
                Extract the locations from the text that it appears the user and assistant are interested in.
                - It should be a comma seperated list of the locations in single quotes.
                - The content should not include start and end headers.
                - It should be in a single line.

                TEXT: "{text}".
            
        """
        messages = [
            {"role": "user", "content": prompt}
        ]
        response = chat_provider.complete_chat(messages)
        locations = response.content
        chat_messages.add_flowdata(self.flowdata_key, locations)

        return chat_messages


    def process(self, messages: ChatFlowMessages) -> ChatFlowMessages:
        """Process the messages and return the updated list of messages."""
        self.extract_locations_from_text_using_llm(messages)
        return messages    

class LocationFilterNode(ChatFlowNode):
    """
    Look up the geometry for the identified locations.
    """
    
    def __init__(self):
        super().__init__("Location Filter Node")
    

    WHERECLAUSE_TEMPLATE = "WHERE ST_Distance(geom, ST_GeomFromText('{geometry}', 3857)) < 2000"

    def filter_locations(self, chat_messages: ChatFlowMessages) -> ChatFlowMessages:
        """Filter the locations to get the geometry for each location."""
        try:
            locations = chat_messages.get_flowdata("location_extract_node")
        except KeyError:
            print("No locations found in the flowdata.")
            return chat_messages
        
        split_locations = locations.split(",")
        locations = [location.strip() for location in split_locations]

        all_wkt_points = []
        for location in locations:
            features = geometry_return(location)
            for feature in features["results"]:
                # prep for multipoint geometry
                feature["geometry"] = feature["geometry"].replace("POINT", "")
                all_wkt_points.append(feature["geometry"])


        # convert the WKT Geometries to a muktipoint geometry
        geometry = "MULTIPOINT(" + ", ".join(all_wkt_points) + ")"
        whereclause = self.WHERECLAUSE_TEMPLATE.format(geometry=geometry)
        
        chat_messages.add_flowdata(self.flowdata_key, whereclause)
        return chat_messages

    def process(self, messages: ChatFlowMessages) -> ChatFlowMessages:
        """Process the messages and return the updated list of messages."""
        self.filter_locations(messages)
        return messages
        
    

def geometry_return(name_to_search: str) -> Dict[str, List]:
        
    #Featureservice numbers relate to the following datasets:
    # 4 - Ceremonial Counties
    # 5 - Districts, Metropolitan districts, London boroughs, Unitary authorities
    # 6 - Civil parishes and communities
    # 7 - Wards
    # 9 - Counties
    # 11 - Westminster constituencies
    
    featureservice_numbers = [4, 5, 6, 7, 9, 11]

    # Base URL for the ArcGIS REST API for OS Open Boundary Line
    # TODO: Move this to a settings file
    base_url = "https://services.arcgis.com/qHLhLQrcvEnxjtPr/ArcGIS/rest/services/OS_OpenBoundaryLine/FeatureServer/{}/query?where=NAME LIKE '%25" + name_to_search + "%25'&outFields=NAME,DESCRIPTIO,&returnGeometry=true&returnIdsOnly=false&f=geojson"
    
    
    results = []
    for number in featureservice_numbers:
        print(f"Searching for {name_to_search} in featureservice {number}")
        
        current_url = base_url.format(number)
        response = requests.get(current_url)

        
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            print(data)

            if len(data["features"]) > 0:
                for feature in data["features"]:
                    geometry = feature["geometry"]
                    if geometry:
                        geometryGeos = GEOSGeometry(json.dumps(geometry), srid=4326)
                        geometryGeos.transform(3857)
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
        return {"results": []}
    
    return {"results": results}