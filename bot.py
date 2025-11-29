import sys
# 1. FORCE UTF-8
sys.stdout.reconfigure(encoding='utf-8')

import os
import random 
import requests
import tweepy
import google.generativeai as genai
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
X_CONSUMER_KEY = os.getenv("X_API_KEY")
X_CONSUMER_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

# --- TOPIC LIST ---
TOPICS = [
    # --- NATURE & BIOLOGY ---
    "The Deep Sea", "Bioluminescence", "Fungi & Mycology", "Carnivorous Plants", 
    "Extremophiles", "Animal Camouflage", "Venomous Creatures", "Bird Migration", 
    "The Amazon Rainforest", "Coral Reefs", "Ant Colonies", "Wolf Packs", 
    "Whale Communication", "Insect Swarms", "Parasites", "Symbiosis",
    "Ancient Trees", "Octopuses", "Crows & Ravens", "Jellyfish", 
    
    # --- SPACE & PHYSICS ---
    "Black Holes", "Neutron Stars", "The Mars Rover", "The ISS", 
    "Dark Matter", "Solar Flares", "Exoplanets", "Time Dilation", 
    "Quantum Entanglement", "The Big Bang", "Supernovas", "Asteroids", 
    "Saturn's Rings", "Voyager Probes", "Light Speed", "Gravity",
    
    # --- ANCIENT HISTORY ---
    "Ancient Egypt", "The Maya Civilization", "The Aztecs", "The Incas", 
    "Samurai Culture", "Spartan Warriors", "The Silk Road", "The Library of Alexandria", 
    "Viking Lore", "Roman Gladiators", "Mesopotamia", "The Bronze Age Collapse", 
    "Ancient Greek Inventions", "The Great Wall of China", "Stonehenge", "Petra",
    
    # --- WEIRD HISTORY & MYSTERY ---
    "The Mary Celeste", "The Dancing Plague of 1518", "Jack the Ripper", 
    "The Zodiac Killer", "The Bermuda Triangle", "Lost Cities", "Alchemy", 
    "Victorian Era Poisons", "The Salem Witch Trials", "Espionage Gadgets", 
    "Cryptids", "Unsolved Heists", "Ghost Ships", "Secret Societies",
    
    # --- SCIENCE & TECH ---
    "Artificial Intelligence", "Nanotechnology", "Robotics", "Cybersecurity", 
    "The Internet's History", "Video Game History", "Cryptography", "Nuclear Energy", 
    "3D Printing", "Virtual Reality", "Space Elevators", "Biotech",
    
    # --- EARTH & GEOGRAPHY ---
    "Volcanoes", "Tectonic Plates", "The Dead Sea", "Mount Everest", 
    "Antarctica", "The Sahara Desert", "Caves & Spelunking", "Tsunamis", 
    "Tornadoes", "The Aurora Borealis", "Glaciers", "Geysers",
    
    # --- CULTURE & ARTS ---
    "Surrealism", "The Renaissance", "Film Noir", "Ancient Pottery", 
    "Origami", "Calligraphy", "Gothic Architecture", "Steampunk", 
    "Cyberpunk", "Mythology", "Urban Legends", "Coffee History"
]

def clean_text(text):
    """Sanitizes text: removes bolding (**), bullets, dashes, quotes."""
    text = text.replace("**", "") 
    return text.strip().lstrip("-•*> \"'")

def get_gemini_content():
    """Generates a Simple, Interesting Fact."""
    # 1. Pick a random topic
    chosen_topic = random.choice(TOPICS)
    print(f"✨ Topic Selected: {chosen_topic}")
    print("✨ Asking Gemini for content...")
    
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # --- PROMPT ---
    full_prompt = (
        f"ACT AS: A teacher of interesting trivia.\n"
        f"TASK: Write one fascinating fact specifically about: {chosen_topic}.\n\n"

        "--- PART 1: THE FACT (Text) ---\n"
        "POSITIVE CONSTRAINTS:\n"
        "- Content: Simple, educational, and verified.\n"
        "- Style: Clear and direct sentences.\n"
        "- STRICTLY under 240 characters.\n"
        "NEGATIVE CONSTRAINTS:\n"
        "- NO 'Did you know' (I will add it later).\n"
        "- NO Emojis.\n"
        "- NO Dashes/Bullets.\n"
        "- NO Markdown bolding (**).\n"
        "- NO Horror, gore, or overly complex irony.\n\n"

        "--- PART 2: THE IMAGE PROMPT (Visual) ---\n"
        "Write a prompt for an AI image generator (Flux).\n"
        "Constraint: Photorealistic, National Geographic style, Cinematic lighting, 8k.\n\n"

        "FORMAT: FACT ||| IMAGE_PROMPT"
    )
    
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
    """Generates image using Pollinations/Flux."""
    print(f"🎨 Generating Image: '{prompt}'...")
    
    final_prompt = f"{prompt}, hyper-realistic, cinematic lighting, 8k, highly detailed"
    encoded_prompt = urllib.parse.quote(final_prompt)
    
    # Random seed ensures unique images
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&model=flux&seed={random.randint(1, 1000)}&nologo=true"
    
    try:
        response = requests.get(url, timeout=45)
        if response.status_code == 200:
            filename = "temp_ai_image.jpg"
            with open(filename, 'wb') as handler:
                handler.write(response.content)
            print("⬇️  Image downloaded.")
            return filename
        else:
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
        
        # 4. Construct Tweet (Emoji Removed)
        tweet_text = f"Did you know? {fact}\n\n#HawkFacts #Facts #Learning"
        
        # Safety Truncation (Emoji Removed)
        if len(tweet_text) > 270:
             tweet_text = f"Did you know? {fact}\n\n#HawkFacts"

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
