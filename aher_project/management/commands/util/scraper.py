import shutil
import os
import json
import logging
import requests
from typing import List, Dict

HOST_URL = "http://localhost:8000"
GLHER_URL = "https://glher.historicengland.org.uk"
RESOURCES_URL = f"{HOST_URL}/resources/?page="
GRAPHS_URL = f"{HOST_URL}/graphs/?format=json"
DOC_STORE_PATH = os.path.join(os.getcwd(), "doc_store")

def save_to_doc(string_data, filename, extension=".txt"):
    if not os.path.exists(DOC_STORE_PATH):
        os.makedirs(DOC_STORE_PATH)
    full_file_path = os.path.join(DOC_STORE_PATH, f"{filename}{extension}")
    with open(full_file_path, 'w') as f:
        f.write(string_data)


def fetch_url(url: str) -> requests.Response:
    """
    Fetch a URL using requests
    
    :param url: The URL to fetch
    :return: The response or None if there was an error
    """
    try:
        response = requests.get(url)
        return response
    except Exception as e:
        logging.error(f"Error fetching URL {url}: {str(e)}")
        return None

#def extract_text_from_html(html: str):
#    '''
#    Extracts text from an HTML string
#    
#    :param html: The HTML string
#    :return: The extracted text
#    '''
#    # use beautifulsoup to extract text from html
#    try:
#        soup = BeautifulSoup(html, "html.parser")
#        text = soup.get_text()
#        return text
#    except ImportError:
#        logging.error("BeautifulSoup is not installed. Please install it using 'pip install beautifulsoup4'")
#        return None
#    except Exception as e:
#        logging.error(f"Error extracting text from HTML: {str(e)}")
#    return None

#def scrape_index_page():
#    response = fetch_url(HOST_URL)
#    if not response or response.status_code == 500:
#        logging.error("500 error fetching index page")
#        return None
#
#    index_text = extract_text_from_html(response.text)
#    save_to_doc(index_text, "index_page")
#    
#    #index_chunks = chunck_index_page(index_text)
#    #print(index_chunks)
#    #index_to_vectorstore(index_chunks)
#    print("Index page scraped and added to vector store")

#def chunck_index_page(index_content: str):
#
#    if not index_content:
#        logging.error("No index page found")
#        return None
#    return chunk_data(index_content, 1000, 200)

#def index_to_vectorstore(index_chunk_lit: list):
    #Chroma.from_texts(texts=index_chunk_lit, embedding=OLLAMA_EMBEDDINGS, persist_directory=CHROMA_STORE_PATH).persist()

def fetch_graphs():
    response = fetch_url(GRAPHS_URL)
    if not response or response.status_code == 500:
        logging.error("500 error fetching graphs")
        return {}
    
    data = response.json()
    graphs = {}
    for graph in data:
        #if graph["isactive"] and graph["isresource"]:
        if graph["isresource"]:
            if graph["name"] != "Arches System Settings":
                graphs[graph["graphid"]] = {
                    "graph_name": graph["name"],
                    "graph_description": graph["description"]
                }
    return graphs

def fetch_resourceids(page: int):
    url = f"{RESOURCES_URL}{page}"
    #print(url)
    response = fetch_url(url)
    print(f"fetching page {page}: {url}")
    if not response or response.status_code == 500:
        print(f"500 error fetching resource list for page {page}")
        logging.error(f"500 error fetching resource list for page {page}")
        return []
    
    data = response.json()
    #print(data)
    urls = data["ldp:contains"]
    return [url.split("/")[-1] for url in urls]

def fetch_resource(resourceinstanceid: str):
    url = f"{HOST_URL}/resources/{resourceinstanceid}?format=json"
    #print(url)
    response = fetch_url(url)
    if not response or response.status_code != 200:
        logging.error(f"Error fetching resource {resourceinstanceid}: code {response.status_code}")
        return None
    
    try:
        data = response.json()
        if GRAPH_DICT:
            graphid = data["graph_id"]
            if graphid in GRAPH_DICT:
                data["graph_name"] = GRAPH_DICT[graphid]["graph_name"]
        #data["document_url"] = f"{HOST_URL}/report/{resourceinstanceid}"
        data["document_url"] = f"{GLHER_URL}/report/{resourceinstanceid}"
        return data
    except Exception as e:
        logging.error(f"Error parsing JSON for resource {resourceinstanceid}: {str(e)}")
        return None

#3def chunk_data(data: str, chunk_size: int, overlap: int = 0):
#3    '''
#3    Chunks a string into smaller strings of a given size with optional overlap
#3    
#3    :param data: The string to chunk
#3    :param chunk_size: The size of the chunks
#3    :param overlap: The number of characters to overlap between chunks
#3    :return: A list of strings
#3    '''
#3    if chunk_size == 0 and overlap == 0:
#3        return [data]
#3
#3    chunks = []
#3    for i in range(0, len(data), chunk_size - overlap):
#3        chunk = data[i:i + chunk_size]
#3        chunks.append(chunk)
#3        if i + chunk_size >= len(data):
#3            break
#3    return chunks

def page_crawler(page: int, store_path: str) -> bool:
    '''
    Fetches resources from a given page and stores them in the vector store
    
    :param page: The page number to fetch resources from
    :param store_path: The path to the vector store
    :return: True if resources were fetched and stored successfully, False meaning max page reached
    
    '''
    resources = fetch_resourceids(page)

    if not resources:
        logging.error(f"No resources found on page {page}")
        return False

    # if RESOURCE_LIMIT is great than 0 then trim the resources list to the limit
    if RESOURCE_LIMIT > 0:
        resources = resources[:RESOURCE_LIMIT]

    for resource in resources:
        try:
            #text_chunks = [] 
            data = fetch_resource(resource)
            if data:
                data = remove_empty_dict_items(data)
                #print(data)
                stringData = json.dumps(data)
                save_to_doc(stringData, f"{resource}", extension=".json") 
                #stringData = convert_json_to_report(stringData)
                #save_to_doc(stringData, f"{resource}")
                #chunks = chunk_data(stringData, 1000, 200)
                #chunks = chunk_data(stringData, 0, 0)
                #for chunk in chunks:
                #    text_chunks.append(chunk)
            
            #if text_chunks:
                #Chroma.from_texts(texts=text_chunks, embedding=OLLAMA_EMBEDDINGS, persist_directory=store_path).persist()
        except Exception as e:
            logging.error(f"Error processing {resource}: {str(e)}")
            continue

    return True


GRAPH_DICT = None

IGNORE_KEYS = [
        "valueid",
        "concept_id",
        "language_id",
        "valueid",
        "valuetype_id",
        "instance_details",
        "direction",
        "Geospatial Coordinates",
        "inverseOntologyProperty",
        "ontologyProperty",
        "resourceId",
        "resourceXresourceId",
        "legacyid",
        "map_popup",
        "concept_details",
        "@display_value"
]
def remove_empty_dict_items(d: Dict):
    '''
    Remove empty items from a dictionary
    '''
    if not isinstance(d, (dict, list)):
        return d
    if isinstance(d, list):
        return [v for v in (remove_empty_dict_items(v) for v in d) if v]
    return {k: v for k, v in ((k, remove_empty_dict_items(v)) for k, v in d.items()) if v and not k in IGNORE_KEYS and v not in ["null", "Undefined"] and "Metatype" not in str(k)}
            

#def convert_json_to_report(document_content: str):
#    '''
#    Convert a document to a report using Ollama
#    
#    :param document_content: The content of the document
#    :return: The generated report
#    '''
#
#    prompt = f"""Format the JSON content as a markdown document, following these rules:
#
#        # Resource Report: [display_name]
#
#        ## Overview
#        - Display Name: [value]
#        - Display Description: [value] 
#        - Graph Name: [value]
#        - Document URL: [value]
#
#        ## Details
#        [Convert remaining key-value pairs using these rules:]
#        - Use ### for top-level headings
#        - Use #### for nested headings
#        - Format lists with bullet points (-)
#        - Create tables for structured data
#
#        Rules:
#        - All the data must be included in the report
#        - Output only markdown text
#        - Exclude null/empty values
#        - Exclude geospatial coordinates
#        - Prefer values from "@value" or "display_value" fields
#        - Use nested headings for nested JSON objects
#        - No AI commentary or explanations
#
#        JSON INPUT:
#        {document_content}
#    """
#    
#    return OLLAMA_SUMMARIZER.predict(prompt)


def run_graph_crawler(store_path: str):
    '''
    Fetch information about the graphs and store them in the vector store
    '''
    global GRAPH_DICT
    GRAPH_DICT = fetch_graphs()

    if not GRAPH_DICT:
        logging.error("No graphs found")
        return
    
    for graphid, graph in GRAPH_DICT.items():
        try:
            #text_chunks = []
            stringData = json.dumps(graph)
            save_to_doc(stringData, f"graph_{graphid}", extension=".json")
            #chunks = chunk_data(stringData, 1000, 200) # modded to just do the whole document.
            #    text_chunks.append(chunk)
            ##for chunk in chunks:
            #print(text_chunks)            
            #if text_chunks:
            #    Chroma.from_texts(texts=text_chunks, embedding=OLLAMA_EMBEDDINGS, persist_directory=store_path).persist()
        except Exception as e:
            logging.error(f"Error processing {graphid}: {str(e)}")
            continue

    print("Graphs fetched")
    #print("Graphs fetched and added to vector store")



###########

#START_PAGE = 1
START_PAGE = 1
#MAX_PAGES = 1
MAX_PAGES = 9999999999
RESOURCE_LIMIT = 0 # 0 = no limit

def main():
       
    #scrape_index_page()

    #run_graph_crawler("CHROMA_STORE_PATH")
    run_graph_crawler("empty")

    page = START_PAGE
    #while page <= MAX_PAGES and page_crawler(page, CHROMA_STORE_PATH):
    while page < MAX_PAGES:
        print(f"Processing page {page}")
        ret = page_crawler(page, "empty")
        page += 1
        if not ret:
            break

if __name__ == "__main__":
    main()