
from qdrant_client import QdrantClient
import json
from sentence_transformers import SentenceTransformer
import streamlit as st

def client_model():
    qdrant_client = QdrantClient(
        url="https://4341ac7b-ffd3-4a57-8408-cf157cdfb9eb.europe-west3-0.gcp.cloud.qdrant.io:6333", 
        api_key="t21ieDMt7FRFM0kSSLyRZhR4sFvIXeCQ9SXfiMbOalFo4p4aaUpE-Q"
    )
    return qdrant_client

encoder = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(":memory:")



# Open the JSON file
def readJson(filename):
    with open(filename, 'r') as file:
        # Load the JSON data into a dictionary
        documents = json.load(file)
    return documents

points = []

from qdrant_client.http import models
from qdrant_client.http.models import PointStruct
client.create_collection(
    collection_name="my_books",
    vectors_config=models.VectorParams(
        size=encoder.get_sentence_embedding_dimension(),  # Vector size is defined by used model
        distance=models.Distance.COSINE, 
    ),
)

def encoding():
    for idx, doc in enumerate(readJson('1.json')):
        vector = encoder.encode(doc["event_desc"]).tolist()
        point = models.PointStruct(
            id=idx, vector=vector, payload=doc
        )
        points.append(point)
    client.upload_points(
        collection_name="my_books",
        points= points,
    )
    
def search(search_query, num):
    encoding()
    hits = client.query_points(
        collection_name="my_books",
        query=encoder.encode(" ".join(search_query)).tolist(),
        limit=num,
    ).points
    for hit in hits:
        print(hit.payload, "score:", hit.score)
        st.markdown(f'''
    #### {hit.payload['event_title']}
    **{hit.payload['event_org']}** \n 
    **Date:** {hit.payload['date']} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **location:** {hit.payload['loc']}
''')
        st.write(hit.payload['event_desc'])




st.title("EventConnect - IITD")
search_query = st.text_input('',placeholder="Enter text to search")
if (len(search_query.strip())>1):
    search(search_query,3)

# Streamlit
#sidebar
st.sidebar.header("Filters")
options = st.sidebar.multiselect('Tell your preferences:', ['Tech', 'Cultural', 'Academic', 'ARIES', 'EDC', 'OCS', 'IGTS'], ['Tech', 'EDC', 'IGTS'])
#displaying the selected options
st.header("Recommendations")

search(options, 5)
