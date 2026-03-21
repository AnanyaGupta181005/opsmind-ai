import os
import google.generativeai as genai
from typing import Dict, Any
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Configuration using environment variables (No hardcoded keys)
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

def search_database(collection_name: str, query_parameters: Dict[str, Any]):
    """
    Industry Standard Tool: Converts NL to structured queries.
    Integration point for Phase 1 (users.csv) or Phase 2 (MongoDB).
    
    Args:
        collection_name: The name of the database collection (e.g., 'users', 'logs').
        query_parameters: A dictionary of filters.
        
    Examples of query_parameters:
        {"department": "IT", "status": "active"}
        {"role": "admin", "last_login": {"$gt": "2023-01-01"}}
    """
    print(f"--- [AGENT ACTION] Searching {collection_name} with params: {query_parameters} ---")
    
    # In production, this would call your FastAPI endpoint or Mongo driver
    # Example: return requests.get(f"{API_URL}/search", params=query_parameters).json()
    return [{"status": "Success", "data": "Found 3 active users in IT"}]

# Initialize the Generative Model with tools
model = genai.GenerativeModel('models/gemini-3-flash-preview',
    tools=[search_database],
    system_instruction=(
        "You are a database admin. Convert user questions into structured Mongo-style queries. "
        "Use the 'search_database' tool for every request regarding data lookup."
    )
)

# Start a chat session with automatic function calling enabled
chat = model.start_chat(enable_automatic_function_calling=True)

# Test execution with Error Handling
if __name__ == "__main__":
    user_query = "Find all active users in the IT department."
    
    try:
        # [CRITICAL]: Wrapped Agent execution to catch API or Tool errors
        response = chat.send_message(user_query)
        print(f"Final Agent Response: {response.text}")
    except Exception as e:
        print(f"CRITICAL ERROR: Agent failed to execute.\nDetails: {e}")