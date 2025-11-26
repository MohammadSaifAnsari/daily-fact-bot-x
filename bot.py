import sys
# 1. FORCE UTF-8: Fixes the "UnicodeEncodeError" on Windows/VS Code
sys.stdout.reconfigure(encoding='utf-8')

import os
import requests
import tweepy
import google.generativeai as genai
from datetime import datetime # <--- NEW IMPORT FOR TIME
from dotenv import load_dotenv

# 2. Load environment variables
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
    Asks Gemini for a fact relevant to TODAY'S DATE.
    """
    # Get today's date (e.g., "November 26")
    today_date = datetime.now().strftime("%B %d")
    
    print(f"✨ Asking Gemini for a fact about: {today_date}...")
    
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # --- TREND JACKING PROMPT ---
        prompt = (
            f"Current Date: {today_date}. "
            "Write a mind-blowing 'On This Day' fact about a historical event, scientific discovery, "
            "or person born on this specific date. "
            "Tone: Exciting, Storyteller. "
            "Constraint: Strictly under 220 characters. "
            "If nothing significant happened on this date, provide a random obscure science fact instead. "
            "\n\n"
            "After the fact, provide a single VISUAL keyword for the image search. "
            "Format: FACT ||| KEYWORD"
        )
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        if "|||" in text:
            fact, keyword = text.split("|||")
            fact = fact.strip()
            keyword = keyword.strip()
            
            # Clean up keyword
            keyword = keyword.replace(".", "").replace('"', "")
            
            return fact, keyword
        else:
            return text, "galaxy"
            
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return None, None

def get_image_from_unsplash(keyword):
    """
    Downloads a random image for the keyword.
    """
    print(f"📸 Searching Unsplash for: '{keyword}'...")
    url = "https://api.unsplash.com/photos/random"
    params = {
        "query": keyword,
        "orientation": "landscape",
        "client_id": UNSPLASH_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        
        # Fallback if specific keyword fails
        if response.status_code != 200:
            print(f"⚠️ Specific keyword '{keyword}' not found. Trying 'nature' fallback...")
            params["query"] = "nature"
            response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            image_url = data['urls']['regular']
            
            # Download binary content
            img_data = requests.get(image_url).content
            filename = "temp_post_image.jpg"
            
            with open(filename, 'wb') as handler:
                handler.write(img_data)
            
            print("⬇️  Image downloaded successfully.")
            return filename
        else:
            print(f"❌ Unsplash API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Image Download Error: {e}")
        return None

def main():
    print("--- 🤖 Daily Fact Bot (Trend Jacking Mode) Starting ---")

    # Step 1: Get Content (Now Date-Aware)
    fact, keyword = get_gemini_content()
    if not fact:
        print("Aborting: Failed to generate fact.")
        return

    print(f"📝 Fact: {fact}")
    print(f"🔍 Keyword: {keyword}")

    # Step 2: Get Image
    image_path = get_image_from_unsplash(keyword)
    if not image_path:
        print("Aborting: Failed to download image.")
        return

    # Step 3: Authenticate to X
    try:
        print("🔐 Authenticating with X...")
        
        # v1.1 API (For Media Upload)
        auth = tweepy.OAuth1UserHandler(
            X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
        )
        api_v1 = tweepy.API(auth)

        # v2 Client (For Posting Tweet)
        client_v2 = tweepy.Client(
            consumer_key=X_CONSUMER_KEY,
            consumer_secret=X_CONSUMER_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_SECRET
        )

        # Step 4: Upload Media
        print("📤 Uploading media...")
        media = api_v1.media_upload(filename=image_path)
        media_id = media.media_id

        # Step 5: Post Tweet
        print("🐦 Posting tweet...")
        clean_tag = keyword.replace(" ", "")
        
        # Dynamic Hashtag based on logic
        today_tag = datetime.now().strftime("#%B%d") # e.g. #November26
        tweet_text = f"{fact}\n\n#{clean_tag} {today_tag} #OnThisDay"

        response = client_v2.create_tweet(text=tweet_text, media_ids=[media_id])
        print(f"✅ SUCCESS! Tweet sent. ID: {response.data['id']}")

    except Exception as e:
        print(f"❌ Twitter Error: {e}")

    finally:
        # Step 6: Cleanup
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
            print("🧹 Temporary image file deleted.")
        print("--- End of Script ---")

if __name__ == "__main__":
    main()
