import sys
# 1. FIX: Force UTF-8 encoding for VS Code/Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

import os
import requests
import tweepy
import google.generativeai as genai
from dotenv import load_dotenv

# Load keys from .env file
load_dotenv()

# --- CONFIGURATION ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
X_CONSUMER_KEY = os.getenv("X_API_KEY")
X_CONSUMER_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

def get_gemini_content():
    """
    Returns a tuple: (fact_text, keyword_for_image)
    """
    print("✨ Asking Gemini for a fact...")
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = (
        "Generate a fascinating, verified fact about nature, history, or science. "
        "Then, provide a single, simple keyword to search for an image of that fact. "
        "Format your response exactly like this: FACT ||| KEYWORD. "
        "Keep the fact under 200 characters. No hashtags in the response."
    )
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "|||" in text:
            fact, keyword = text.split("|||")
            return fact.strip(), keyword.strip()
        else:
            return text, "nature" # Fallback
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return None, None

def get_image_from_unsplash(keyword):
    """
    Searches Unsplash and downloads a random image.
    """
    print(f"📸 Searching Unsplash for: {keyword}...")
    url = "https://api.unsplash.com/photos/random"
    params = {
        "query": keyword,
        "orientation": "landscape",
        "client_id": UNSPLASH_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            image_url = data['urls']['regular']
            
            # Download the image
            img_data = requests.get(image_url).content
            with open('temp_image.jpg', 'wb') as handler:
                handler.write(img_data)
            print("⬇️  Image downloaded.")
            return 'temp_image.jpg'
        else:
            print(f"❌ Unsplash Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Image Download Error: {e}")
        return None

def run_test_post():
    print("--- 🚀 Starting Test Run ---")
    
    # 1. Get Content
    fact, keyword = get_gemini_content()
    if not fact:
        print("Stopping: No content generated.")
        return

    print(f"📝 Fact: {fact}")

    # 2. Get Image
    image_path = get_image_from_unsplash(keyword)
    if not image_path:
        print("Stopping: No image found.")
        return

    # 3. Authenticate to X
    print("🔐 Authenticating with X...")
    try:
        # V1.1 Auth (For Media Upload)
        auth = tweepy.OAuth1UserHandler(
            X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
        )
        api = tweepy.API(auth)

        # V2 Auth (For Posting Text)
        client = tweepy.Client(
            consumer_key=X_CONSUMER_KEY,
            consumer_secret=X_CONSUMER_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_SECRET
        )

        # 4. Upload Image
        print("📤 Uploading image to X...")
        media = api.media_upload(filename=image_path)
        media_id = media.media_id

        # 5. Post Tweet
        print("🐦 Posting tweet...")
        tweet_text = f"{fact}\n\n#{keyword.replace(' ', '')} #DailyFact #DidYouKnow"
        
        response = client.create_tweet(text=tweet_text, media_ids=[media_id])
        print(f"✅ SUCCESS! Tweet ID: {response.data['id']}")
        
        # Cleanup
        os.remove(image_path)
        print("🧹 Cleaned up temporary files.")
        
    except Exception as e:
        print(f"❌ Twitter Post Error: {e}")

if __name__ == "__main__":
    # This runs the function immediately, once.
    run_test_post()