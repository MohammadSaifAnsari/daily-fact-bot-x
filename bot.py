import sys
# 1. FORCE UTF-8: Fixes the "UnicodeEncodeError" on Windows/VS Code
sys.stdout.reconfigure(encoding='utf-8')

import os
import requests
import tweepy
import google.generativeai as genai
from dotenv import load_dotenv

# 2. Load environment variables
# (Works locally with .env file, and works on GitHub Actions using Secrets)
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
    Asks Gemini for a Fact and a Keyword.
    Returns: (fact_text, keyword)
    """
    print("✨ Asking Gemini for content...")
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = (
            "Generate a fascinating, verified fact about nature, history, space, or science. "
            "Then, provide a single, simple English keyword to search for an image of that fact. "
            "Format your response exactly like this: FACT ||| KEYWORD. "
            "Keep the fact under 200 characters. Do not include hashtags."
        )
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        if "|||" in text:
            fact, keyword = text.split("|||")
            return fact.strip(), keyword.strip()
        else:
            # Fallback if Gemini messes up the format
            return text, "science"
            
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return None, None

def get_image_from_unsplash(keyword):
    """
    Downloads a random image for the keyword.
    Returns: path to the saved image file.
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
    print("--- 🤖 Daily Fact Bot Starting ---")

    # Step 1: Get Text Content
    fact, keyword = get_gemini_content()
    if not fact:
        print("Aborting: Failed to generate fact.")
        return

    print(f"📝 Fact: {fact}")

    # Step 2: Get Image
    image_path = get_image_from_unsplash(keyword)
    if not image_path:
        print("Aborting: Failed to download image.")
        return

    # Step 3: Authenticate to X (Twitter)
    try:
        print("🔐 Authenticating with X...")
        
        # v1.1 API (Required for Media Upload)
        auth = tweepy.OAuth1UserHandler(
            X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
        )
        api_v1 = tweepy.API(auth)

        # v2 Client (Required for Posting Tweet)
        client_v2 = tweepy.Client(
            consumer_key=X_CONSUMER_KEY,
            consumer_secret=X_CONSUMER_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_SECRET
        )

        # Step 4: Upload Media
        print("outbox_tray Uploading media...")
        media = api_v1.media_upload(filename=image_path)
        media_id = media.media_id

        # Step 5: Post Tweet
        print("🐦 Posting tweet...")
        # Clean up keyword for hashtag (remove spaces)
        clean_tag = keyword.replace(" ", "")
        tweet_text = f"{fact}\n\n#{clean_tag} #DailyFact #Learning"

        response = client_v2.create_tweet(text=tweet_text, media_ids=[media_id])
        print(f"✅ SUCCESS! Tweet sent. ID: {response.data['id']}")

    except Exception as e:
        print(f"❌ Twitter Error: {e}")

    finally:
        # Step 6: Cleanup (Always run this)
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
            print("🧹 Temporary image file deleted.")
        print("--- End of Script ---")

if __name__ == "__main__":
    main()

