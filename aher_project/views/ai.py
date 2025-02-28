from django.views.generic import View
from django.http import JsonResponse
import requests
import json
from django.contrib.gis.geos import GEOSGeometry, WKTWriter

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
                            wkt_writer = WKTWriter()
                            wkt_geometry = wkt_writer.write(geometryGeos).decode('utf-8') 
                            
                            feature_data = {}
                            feature_data["geometry"] = wkt_geometry
                            feature_data["name"]= feature["properties"]["NAME"] 
                            feature_data["description"] = feature["properties"]["DESCRIPTIO"]
                            results.append(feature_data)
            else:
                print(f"Failed to retrieve data: {response.status_code}")
                
        if len(results) > 0:
            return results
        
        
class ChatAPIView(View):
    
    def get(self, request):
        response = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean a interdum nibh, eget semper nunc. Donec pharetra, risus ac ornare volutpat, dolor mauris finibus sapien, quis sagittis nunc augue ut ipsum. Nunc eu tortor vitae enim blandit facilisis quis ultricies sapien. Proin tempor pharetra est, ut imperdiet tellus eleifend non. Vestibulum id pulvinar ex. Sed elit leo, maximus sit amet sem quis, finibus auctor metus. Donec sit amet ligula nec lectus malesuada feugiat ut sed nulla. Pellentesque cursus pulvinar elit, id dapibus felis rutrum in. Fusce pulvinar lectus vitae urna dapibus, at ultricies turpis ultrices. Integer luctus congue pharetra. Proin quis lorem in libero interdum ultricies quis ut massa. Donec venenatis, enim a pulvinar tincidunt, ligula sem tempor enim, ut commodo arcu mauris ornare turpis. Suspendisse placerat varius sapien, quis pretium turpis semper sit amet. Sed dapibus finibus venenatis. Vestibulum viverra, dui et interdum cursus, lectus mi pharetra nisl, eget dictum tellus eros vel dolor. Sed purus tortor, rutrum id efficitur sed, rhoncus et ante. Aliquam a vehicula metus. Mauris pharetra nisl lorem, in dignissim erat iaculis semper. Aenean lacinia metus justo, eu mollis mauris consequat eget. Vestibulum condimentum porttitor quam, non lacinia dui tempus ac. In cursus sem vel."
        return JsonResponse({"message": response}, status=200)

    def post(self, request):
        return JsonResponse({"message": "This is a blank API view"}, status=200)