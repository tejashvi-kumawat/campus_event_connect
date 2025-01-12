from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import streamlit as st
# from google.colab import userdata
qdrant_client = QdrantClient(
    url="https://4341ac7b-ffd3-4a57-8408-cf157cdfb9eb.europe-west3-0.gcp.cloud.qdrant.io:6333", 
    api_key="t21ieDMt7FRFM0kSSLyRZhR4sFvIXeCQ9SXfiMbOalFo4p4aaUpE-Q"
)

# print(qdrant_client.get_collections())

from sentence_transformers import SentenceTransformer
encoder = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(":memory:")

import json

# Open the JSON file
with open('1.json', 'r') as file:
    # Load the JSON data into a dictionary
    documents = json.load(file)
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

for idx, doc in enumerate(documents):
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
    hits = client.query_points(
        collection_name="my_books",
        query=encoder.encode(search_query).tolist(),
        limit=num,
    ).points

    for hit in hits:
        print()
        st.write(hit.payload['event_desc'])
        st.write(hit.score)


st.title("EventConnect")
st.header("hello")

search_query = st.text_input("Enter text to search")
if (len(search_query.strip())>1):
    search(search_query,3)

#sidebar
st.sidebar.header("Filters")
options = st.sidebar.multiselect('Tell your preferences:', ['Tech', 'Cultural', 'Academic', 'ARIES', 'EDC', 'OCS', 'IGTS'], ['Tech', 'EDC', 'IGTS'])
#displaying the selected options

# st.sidebar.write('You have selected:', options)


st.header("Recommendations")
for entry in options: 
    if len(options)>=3:
        search(entry,1)
    else:
        st.write(entry,3)
# from flask import Flask, render_template

# app = Flask(__name__)

# @app.route('/')
# def home():
#     return render_template('./index.html')  # Assuming index.html is in the 'templates' folder

# if __name__== '__main__':
#     app.run(debug=True)


