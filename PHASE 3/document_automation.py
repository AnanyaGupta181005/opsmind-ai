import os
import asyncio
import PIL.Image
import google.generativeai as genai
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- Exercise A: The Resume/Invoice Parser (Gemini Vision) ---
def parse_document(file_name: str):
    """
    Uses Gemini Vision to extract key fields from a document.
    Paths are built dynamically to avoid hardcoding.
    """
    try:
        # Build path relative to the current script's directory
        base_path = os.path.dirname(__file__)
        image_path = os.path.join(base_path, "uploads", file_name)
        
        if not os.path.exists(image_path):
            return f"Error: File {file_name} not found in uploads folder."

        img = PIL.Image.open(image_path)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        prompt = "Analyze this document. Extract Name, Skills, and Total Amount into a JSON object."
        
        # [CRITICAL]: Wrapped API call in try-except block
        response = model.generate_content(
            [prompt, img],
            generation_config={"response_mime_type": "application/json"}
        )
        return response.text

    except Exception as e:
        # Log this error to your monitoring system in production
        return f"Error processing document {file_name}: {str(e)}"

# --- Exercise B: The Web Automator (Playwright) ---
async def verify_user_on_web(portal_url: str, license_id: str):
    """
    Navigates to a portal and verifies a license number.
    URL and ID are passed as arguments, not hardcoded.
    """
    try:
        async with async_playwright() as p:
            # Launch browser (headless=True for production background tasks)
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Add timeout handling for navigation
            await page.goto(portal_url, timeout=30000)
            
            # Selectors would typically be stored in a config file or env
            await page.fill(os.getenv("WEB_INPUT_SELECTOR", "#search"), license_id)
            await page.click(os.getenv("WEB_SUBMIT_BUTTON", ".btn-submit"))
            
            # Wait for result with timeout
            try:
                await page.wait_for_selector(".result-status", timeout=5000)
                status = await page.inner_text(".result-status")
            except Exception:
                status = "Timeout: Result selector not found."

            await browser.close()
            return f"Verification Result for {license_id}: {status}"
            
    except Exception as e:
        return f"Web Automation Error for {license_id}: {str(e)}"

if __name__ == "__main__":
    # res = parse_document("sample_invoice.jpg")
    # print(res)
    pass