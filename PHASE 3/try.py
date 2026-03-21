import google.generativeai as genai
import os

# Make sure your API key is set in your environment variables
# or uncomment the line below and add it manually:
# genai.configure(api_key="YOUR_API_KEY")

print("Listing available models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)