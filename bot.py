import sys
# 1. FORCE UTF-8: Fixes Windows/VS Code emoji errors
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import requests
import tweepy
import google.generativeai as genai
from datetime import datetime, timezone
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

def clean_text(text):
    """
    Sanitizes text by removing unwanted starting characters.
    """
    # Remove leading dashes, bullets, quotes, or whitespace
    return text.strip().lstrip("-•*> \"'")

def get_bot_mode():
    """
    Decides the 'Mode' based on the current UTC Hour.
    GitHub Actions runs in UTC.
    """
    current_hour = datetime.now(timezone.utc).hour
    
    # Schedule logic (UTC times)
    # India is UTC+5:30. 
    # 03:30 UTC = 9:00 AM IST
    # 08:30 UTC = 2:00 PM IST
    # 14:30 UTC = 8:00 PM IST
    
    if 3 <= current_hour < 5:
        return "ON_THIS_DAY"    # Morning
    elif 8 <= current_hour < 10:
        return "RANDOM_SCIENCE" # Afternoon
    else:
        return "RANDOM_THRILLER" # Evening

def get_gemini_content(mode):
    """
    Generates content using Positive & Negative Constraints.
    """
    print(f"✨ Generating content for mode: {mode}...")
    
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    today_date = datetime.now().strftime("%B %d")

    # 1. Define the Specific Task based on Mode
    if mode == "ON_THIS_DAY":
        topic_instruction = f"Topic: An obscure historical event that happened on {today_date}."
    elif mode == "RANDOM_SCIENCE":
        topic_instruction = "Topic: A weird, biological, or physical anomaly in nature (Not date related)."
    else:
        topic_instruction = "Topic: A dark, mysterious, or suspenseful historical fact (Not date related)."

    # 2. THE MASTER PROMPT (Positive & Negative Constraints)
    full_prompt = (
        f"ACT AS: A master storyteller and photo editor. \n"
        f"{topic_instruction} \n\n"
        
        "--- POSITIVE CONSTRAINTS (DO THIS) ---\n"
        "1. WRITE A MICRO-STORY: Structure the fact as 'Hook -> Action -> Twist'. \n"
        "2. USE ACTIVE VOICE: Subject performs the action (e.g., 'The volcano destroyed the city'). \n"
        "3. BE SPECIFIC: Use exact numbers, dates, and names. \n"
        "4. VISUAL KEYWORD: Provide ONE single, tangible, physical object for the image search. \n"
        "\n"
        
        "--- NEGATIVE CONSTRAINTS (DO NOT DO THIS) ---\n"
        "1. NO FLUFF: Do not start with 'Did you know', 'Imagine this', or 'In the year'. Start directly with the subject. \n"
        "2. NO ABSTRACT IMAGES: Do not use keywords like 'War', 'Love', 'Science', 'History', 'Nature'. These return bad photos. \n"
        "3. NO EMOJIS: Do not include emojis in the text output. \n"
        "4. NO DASHES: Do not start the sentence with a dash (-) or bullet point. \n"
        "\n"
        
        "--- FEW-SHOT EXAMPLES (Follow this pattern) ---\n"
        "Bad Output: Did you know that bees make honey? ||| Nature \n"
        "Good Output: Ancient Egyptian honey found in tombs is still edible after 3,000 years. ||| Sarcophagus \n"
        "Bad Output: - The Titanic sank in 1912. ||| Tragedy \n"
        "Good Output: The Titanic's pool is still filled with water, deep beneath the Atlantic. ||| Shipwreck \n"
        "\n"
        
        "--- FINAL OUTPUT FORMAT ---\n"
        "FACT ||| PHYSICAL_NOUN_KEYWORD"
    )
    
    try:
        response = model.generate_content(full_prompt)
        raw_text = response.text.strip()
        
        if "|||" in raw_text:
            fact, keyword = raw_text.split("|||")
            return clean_text(fact), clean_text(keyword)
        else:
            return raw_text, "galaxy"
            
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return None, None

def get_image_from_unsplash(keyword):
    """Downloads a random image for the keyword."""
    print(f"📸 Searching Unsplash for: '{keyword}'...")
    url = "https://api.unsplash.com/photos/random"
    
    # Advanced Search Params
    params = {
        "query": keyword,
        "orientation": "landscape",
        "content_filter": "high",
        "client_id": UNSPLASH_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        
        # Smart Fallback Logic
        if response.status_code != 200:
            print(f"⚠️ Keyword '{keyword}' failed. Trying generic fallbacks...")
            # If 'Sarcophagus' fails, try 'Museum'
            fallback_map = {
                "sarcophagus": "museum",
                "microscope": "laboratory",
                "nebula": "stars"
            }
            # Use specific fallback if available, else 'landscape'
            fallback_query = fallback_map.get(keyword.lower(), "landscape")
            params["query"] = fallback_query
            response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            image_url = data['urls']['regular']
            img_data = requests.get(image_url).content
            filename = "temp_post_image.jpg"
            with open(filename, 'wb') as handler:
                handler.write(img_data)
            return filename
        else:
            return None
    except Exception as e:
        print(f"❌ Image Error: {e}")
        return None

def main():
    # 1. Determine Mode
    mode = get_bot_mode()
    print(f"--- 🤖 Bot Starting. Mode: {mode} ---")

    # 2. Get Content
    fact, keyword = get_gemini_content(mode)
    if not fact: return

    print(f"📝 Fact: {fact}")
    print(f"🔍 Keyword: {keyword}")

    # 3. Get Image
    image_path = get_image_from_unsplash(keyword)
    if not image_path: return

    # 4. Post to X
    try:
        auth = tweepy.OAuth1UserHandler(
            X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
        )
        api_v1 = tweepy.API(auth)
        client_v2 = tweepy.Client(
            consumer_key=X_CONSUMER_KEY,
            consumer_secret=X_CONSUMER_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_SECRET
        )

        media = api_v1.media_upload(filename=image_path)
        
        # 5. Smart Hashtags & Formatting
        clean_kw = keyword.replace(" ", "")
        
        # Add Emojis here (not in Gemini)
        if mode == "ON_THIS_DAY":
            date_tag = datetime.now().strftime("#%B%d")
            hashtags = f"#{clean_kw} {date_tag} #History"
            emoji = "📅"
        elif mode == "RANDOM_SCIENCE":
            hashtags = f"#{clean_kw} #Science #WeirdFacts"
            emoji = "🧬"
        else:
            hashtags = f"#{clean_kw} #Mystery #Thriller"
            emoji = "🕵️‍♂️"

        tweet_text = f"{fact} {emoji}\n\n{hashtags}"

        response = client_v2.create_tweet(text=tweet_text, media_ids=[media.media_id])
        print(f"✅ SUCCESS! Tweet sent. ID: {response.data['id']}")

    except Exception as e:
        print(f"❌ Twitter Error: {e}")

    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
        print("--- End of Script ---")

if __name__ == "__main__":
    main()
