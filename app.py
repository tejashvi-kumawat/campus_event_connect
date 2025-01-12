from qdrant_client import QdrantClient
import json
from sentence_transformers import SentenceTransformer
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from qdrant_client.http import models
from qdrant_client.http.models import PointStruct

class EventSearch:
    def __init__(self):
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.client = QdrantClient(":memory:")
        self.documents = None
        self.setup_collection()
        
    def setup_collection(self):
        """Initialize Qdrant collection with proper configuration"""
        self.client.create_collection(
            collection_name="my_books",
            vectors_config=models.VectorParams(
                size=self.encoder.get_sentence_embedding_dimension(),
                distance=models.Distance.COSINE,
            ),
        )
        
    def read_json(self, filename):
        """Read and cache JSON data"""
        with open(filename, 'r') as file:
            self.documents = json.load(file)
        return self.documents
    
    def prepare_documents_for_search(self):
        """Prepare document texts for search"""
        return [doc["event_desc"] for doc in self.documents]
    
    def keyword_search(self, query, documents_text):
        """Perform keyword-based search using TF-IDF"""
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents_text)
        query_vector = tfidf_vectorizer.transform([query])
        return cosine_similarity(query_vector, tfidf_matrix).flatten()
    
    def semantic_search(self, query, documents_text):
        """Perform semantic search using sentence embeddings"""
        doc_embeddings = self.encoder.encode(documents_text)
        query_embedding = self.encoder.encode([query])
        return cosine_similarity(query_embedding, doc_embeddings).flatten()
    
    def hybrid_search(self, query, num_results=5, alpha=0.5):
        """Perform hybrid search combining keyword and semantic search"""
        if not self.documents:
            self.read_json('1.json')
            
        documents_text = self.prepare_documents_for_search()
        
        # Get scores from both search methods
        keyword_scores = self.keyword_search(query, documents_text)
        semantic_scores = self.semantic_search(query, documents_text)
        
        # Combine scores
        hybrid_scores = alpha * keyword_scores + (1 - alpha) * semantic_scores
        
        # Get top results
        top_indices = np.argsort(hybrid_scores)[::-1][:num_results]
        results = []
        
        for idx in top_indices:
            results.append({
                'document': self.documents[idx],
                'score': hybrid_scores[idx]
            })
            
        return results

def main():
    st.title("EventConnect")
    
    # Initialize search engine
    search_engine = EventSearch()
    
    # Sidebar filters
    st.sidebar.header("Filters")
    options = st.sidebar.multiselect(
        'Tell your preferences:', 
        ['Tech', 'Cultural', 'Academic', 'ARIES', 'EDC', 'OCS', 'IGTS'],
        ['Tech', 'EDC', 'IGTS']
    )
    
    # Search weight slider
    alpha = st.sidebar.slider(
        'Adjust search balance',
        0.0, 1.0, 0.5,
        help='0 = Pure Semantic Search, 1 = Pure Keyword Search'
    )
    
    # Main search interface
    search_query = st.text_input("Enter text to search")
    
    if len(search_query.strip()) > 1:
        results = search_engine.hybrid_search(search_query, num_results=3, alpha=alpha)
        
        st.header("Search Results")
        for result in results:
            doc = result['document']
            score = result['score']
            
            st.markdown(f"""
            #### {doc['event_title']}
            **Organization:** {doc['event_org']}  
            **Date:** {doc['date']} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **Location:** {doc['loc']}  
            **Relevance Score:** {score:.2f}
            """)
            st.markdown("---")
    
    # Recommendations based on preferences
    if options:
        st.header("Recommendations Based on Preferences")
        for preference in options:
            results = search_engine.hybrid_search(preference, num_results=2, alpha=alpha)
            
            st.subheader(f"Based on '{preference}' preference:")
            for result in results:
                doc = result['document']
                st.markdown(f"""
                #### {doc['event_title']}
                **Organization:** {doc['event_org']}  
                **Date:** {doc['date']} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **Location:** {doc['loc']}
                """)
                st.markdown("---")

if __name__ == "__main__":
    main()
