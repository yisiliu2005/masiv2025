from flask import Flask, request, jsonify
from flask_cors import CORS
from sodapy import Socrata
from dotenv import load_dotenv
import os
import sys
import traceback
from openai import OpenAI
from data_fetcher import get_all_buildings
from llm_processor import process_query

load_dotenv()

api_key = os.getenv("HF_TOKEN")
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=api_key,
)

# Cache for building data
_buildings_cache = None

def get_buildings_cache():
    """Get or fetch buildings data (cached)."""
    global _buildings_cache
    if _buildings_cache is None:
        print("CACHE MISS: Loading building data from API...", flush=True)
        sys.stdout.flush()
        _buildings_cache = get_all_buildings()
        print(f"CACHE LOADED: {len(_buildings_cache)} buildings cached", flush=True)
        sys.stdout.flush()
    return _buildings_cache

app = Flask(__name__)
CORS(app)

# Initialize cache on startup
print("=" * 60, flush=True)
print("SERVER STARTUP: Initializing building data cache...", flush=True)
print("=" * 60, flush=True)
sys.stdout.flush()
_buildings_cache = get_all_buildings()
print(f"SERVER READY: {len(_buildings_cache)} buildings loaded and cached", flush=True)
print("=" * 60, flush=True)
sys.stdout.flush()

@app.route('/')
def home():
    return "Welcome to the Calgary 3D City Dashboard API!"

@app.route('/api/buildings', methods=['GET'])
def buildings():
    """
    GET /api/buildings
    Returns all buildings in the dataset with their attributes.
    """
    try:
        buildings_data = get_buildings_cache()
        return jsonify({
            "data": buildings_data,
            "error": None,
            "message": f"Returned {len(buildings_data)} buildings"
        })
    except Exception as e:
        return jsonify({
            "data": [],
            "error": str(e),
            "message": "Failed to fetch buildings"
        }), 500

@app.route('/api/query', methods=['POST'])
def query_buildings():
    """
    POST /api/query
    Interprets a natural language query and returns matching building IDs.
    
    Request body:
        {
            "query": "buildings over 100 feet tall",
            "api_key": "(optional) Hugging Face API key"
        }
    
    Response:
        {
            "matching_ids": ["12345", "12367"],
            "filter_parsed": {"attribute": "height", "operator": ">", "value": 100},
            "error": null,
            "message": "Found 2 matching buildings"
        }
    """
    try:
        data = request.get_json()
        user_query = data.get("query", "").strip()
        user_api_key = data.get("api_key", "").strip()
        
        if not user_query:
            return jsonify({
                "matching_ids": [],
                "filter_parsed": None,
                "error": "Query cannot be empty",
                "message": "Please provide a query"
            }), 400
        
        # Get buildings data
        buildings_data = get_buildings_cache()
        
        # Process query with LLM (pass optional API key)
        result = process_query(user_query, buildings_data, user_api_key if user_api_key else None)
        
        message = f"Found {len(result['matching_ids'])} matching buildings"
        
        return jsonify({
            "matching_ids": result["matching_ids"],
            "filter_parsed": result["filter_parsed"],
            "error": result["error"],
            "message": message
        })
    except Exception as e:
        print(f"ERROR in /api/query: {e}")
        traceback.print_exc()
        return jsonify({
            "matching_ids": [],
            "filter_parsed": None,
            "error": str(e),
            "message": "Failed to process query"
        }), 500

@app.route('/members')
def members():
    """Legacy endpoint for testing."""
    return {"members": ["Alice", "Bob", "Charlie"]}

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

