import sys
# 1. FORCE UTF-8: Fixes Windows/VS Code emoji errors
sys.stdout.reconfigure(encoding='utf-8')

import os
import requests
import tweepy
import google.generativeai as genai
import urllib.parse
from dotenv import load_dotenv

# 2. Load environment variables
load_dotenv()

# --- CONFIGURATION ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
X_CONSUMER_KEY = os.getenv("X_API_KEY")
X_CONSUMER_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

def clean_text(text):
    """Sanitizes text to remove bullets/dashes/quotes."""
    text = text.replace("**", "")
    return text.strip().lstrip("-•*> \"'")

def get_gemini_content():
    """
    Generates a Fact + Image Description using Positive/Negative Prompts.
    """
    print("✨ Asking Gemini for content...")
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # --- THE MASTER PROMPT ---
    full_prompt = (
        "ACT AS: A historian and cinematic art director.\n"
        "TASK: Create content for a 'Dark History & Weird Science' channel.\n\n"

        "--- PART 1: THE FACT (Text) ---\n"
        "Write one mind-blowing fact. \n"
        "POSITIVE CONSTRAINTS (DO THIS):\n"
        "- Focus on the 'Twist' or 'Irony'.\n"
        "- Use Active Voice (e.g. 'The volcano destroyed...').\n"
        "- STRICTLY under 230 characters.\n"
        "NEGATIVE CONSTRAINTS (DO NOT DO THIS):\n"
        "- NO 'Did you know', 'Imagine', or 'Fun fact'.\n"
        "- NO Emojis in the text.\n"
        "- NO Dashes (-) at the start.\n\n"

        "--- PART 2: THE IMAGE PROMPT (Visual) ---\n"
        "Write a detailed prompt for an AI image generator to draw this scene.\n"
        "POSITIVE CONSTRAINTS:\n"
        "- Describe the lighting, texture, and angle (e.g., 'Cinematic lighting, macro shot, 8k resolution').\n"
        "- Make it look like a National Geographic photograph.\n"
        "NEGATIVE CONSTRAINTS:\n"
        "- NO text inside the image.\n"
        "- NO cartoon styles.\n"
        "- NO split screens.\n\n"

        "FORMAT: FACT ||| IMAGE_PROMPT"
    )
    
    # Retry logic for length
    for attempt in range(3):
        try:
            response = model.generate_content(full_prompt)
            raw_text = response.text.strip()
            
            if "|||" in raw_text:
                fact, img_prompt = raw_text.split("|||")
                fact = clean_text(fact)
                img_prompt = clean_text(img_prompt)
                
                # Length check
                if len(fact) > 215:
                    full_prompt += "\n\nSYSTEM: PREVIOUS FACT WAS TOO LONG. SHORTEN IT."
                    continue 
                
                return fact, img_prompt
            
        except Exception as e:
            print(f"❌ Generation Error: {e}")
            return None, None
            
    return None, None

def generate_ai_image(prompt):
    """
    Generates an image using Pollinations (Flux Model).
    """
    print(f"🎨 Generating Image: '{prompt}'...")
    
    # Enhance prompt for realism
    final_prompt = f"{prompt}, hyper-realistic, cinematic lighting, 8k, highly detailed"
    encoded_prompt = urllib.parse.quote(final_prompt)
    
    # Pollinations API URL (Flux Model)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&model=flux&seed=42&nologo=true"
    
    try:
        response = requests.get(url, timeout=45)
        if response.status_code == 200:
            filename = "temp_ai_image.jpg"
            with open(filename, 'wb') as handler:
                handler.write(response.content)
            print("⬇️  Image downloaded.")
            return filename
        else:
            print(f"❌ AI Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Download Error: {e}")
        return None

def main():
    print("--- 🦅 Hawk Facts Bot Starting ---")

    # 1. Get Content
    fact, img_prompt = get_gemini_content()
    if not fact: return

    print(f"📝 Fact: {fact}")
    print(f"🎨 Prompt: {img_prompt}")

    # 2. Generate Image
    image_path = generate_ai_image(img_prompt)
    if not image_path: return

    # 3. Post to X
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
        
        # 4. Hashtags (NO "AI" TAGS)
        # We use generic, high-traffic tags to look organic
        tweet_text = f"Did you know? {fact} \n\n#HawkFacts #History #Science #Mystery"
        
        # Safety Truncation
        if len(tweet_text) > 270:
             tweet_text = f"Did you know? {fact} \n\n#HawkFacts"

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




