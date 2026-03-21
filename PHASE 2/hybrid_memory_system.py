import os
from dotenv import load_dotenv
from pymongo import MongoClient
from supabase import create_client
from sentence_transformers import SentenceTransformer

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# MongoDB setup (NoSQL user data)
# -------------------------------------------------
mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client[os.getenv("MONGO_DB")]
users_collection = db[os.getenv("MONGO_COLLECTION")]

# -------------------------------------------------
# Supabase setup (Vector database)
# -------------------------------------------------
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# -------------------------------------------------
# Local embedding model setup
# -------------------------------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text):
    """Convert text into a vector embedding"""
    return model.encode(text).tolist()

# -------------------------------------------------
# Store structured user profile in MongoDB
# -------------------------------------------------
def store_user_profile():
    user_profile = {
        "name": "Ananya",
        "role": "Intern",
        "department": "AI/ML",
        "skills": ["Python", "MongoDB", "Vector Search"]
    }
    users_collection.insert_one(user_profile)
    print("✅ User profile stored in MongoDB")

# -------------------------------------------------
# Store employee handbook in Supabase (Vector Search)
# -------------------------------------------------
def store_handbook(sections):
    for section in sections:
        # FIX: Changed table name from "handbook" to "handbook_embeddings"
        supabase.table("handbook_embeddings").insert({
            "content": section,
            "embedding": get_embedding(section)
        }).execute()
    print("✅ Employee handbook stored in Supabase")

# -------------------------------------------------
# Query Supabase using semantic search
# -------------------------------------------------
def query_handbook(question):
    response = supabase.rpc(
        "match_handbook",
        {
            "query_embedding": get_embedding(question),
            "match_count": 1
        }
    ).execute()

    return response.data[0]["content"]

# -------------------------------------------------
# Main execution
# -------------------------------------------------
if __name__ == "__main__":
    store_user_profile()

    handbook_sections = [
        "Employees must wear formal attire from Monday to Thursday.",
        "Fridays are business casual days.",
        "Office hours are from 9 AM to 6 PM."
    ]

    store_handbook(handbook_sections)

    answer = query_handbook("What is the dress code?")
    print("\n🔍 Relevant Handbook Section:")
    print(answer)
