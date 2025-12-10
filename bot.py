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
    # --- 🌌 DEEP SPACE & COSMIC HORROR ---
    "Black Holes", "Neutron Stars", "The Fermi Paradox", "Dark Matter", "The Great Attractor", 
    "Spaghettification", "Rogue Planets", "Gamma-Ray Bursts", "The Boötes Void", "Magnetars", 
    "Time Dilation", "The Heat Death of the Universe", "Exoplanets", "Solar Flares", "White Dwarfs", 
    "The Event Horizon", "Cosmic Microwave Background", "Pulsars", "Quasars", "The Oort Cloud", 
    "Space Junk", "The ISS", "Voyager Probes", "Mars Colonization", "Europa (Moon)", "Titan (Moon)", 
    "Io (Moon)", "Enceladus", "The Kuiper Belt", "Asteroid Impacts", "Supernovas", "Hypernovas", 
    "Antimatter", "Wormholes", "Parallel Universes", "The Multiverse Theory", "String Theory",

    # --- 🐙 WEIRD NATURE & BIOLOGY ---
    "The Deep Sea", "Bioluminescence", "Cordyceps Fungi", "Tardigrades", "Axolotls", 
    "The Platypus", "Mimic Octopuses", "Immortal Jellyfish", "Goblin Sharks", "Anglerfish", 
    "Carnivorous Plants", "Slime Molds", "Parasitic Wasps", "Ant Supercolonies", "Bee Hive Intelligence", 
    "Crow Intelligence", "Whale Songs", "Elephant Memory", "Wolf Pack Dynamics", "Bird Migration", 
    "The Amazon Rainforest", "Coral Reefs", "Mangrove Forests", "Extremophiles", "Hydrothermal Vents", 
    "The Galapagos Islands", "Komodo Dragons", "Poison Dart Frogs", "Electric Eels", "Vampire Bats", 
    "Naked Mole Rats", "Pangolins", "Narwhals", "Giant Squids", "Colossal Squids", "Sperm Whales",

    # --- 🏛️ ANCIENT CIVILIZATIONS & RUINS ---
    "Ancient Egypt", "The Pyramids of Giza", "The Sphinx", "Valley of the Kings", "Tutankhamun", 
    "The Maya Civilization", "Chichen Itza", "The Aztecs", "Tenochtitlan", "Human Sacrifice Rituals", 
    "The Incas", "Machu Picchu", "The Olmecs", "Mesopotamia", "Sumerian Mythology", "Babylon", 
    "The Hanging Gardens", "Ancient Rome", "The Colosseum", "Pompeii", "Herculaneum", "Roman Gladiators", 
    "Spartan Warriors", "Ancient Greece", "The Parthenon", "The Oracle of Delphi", "Alexander the Great", 
    "The Library of Alexandria", "The Bronze Age Collapse", "The Sea Peoples", "Göbekli Tepe", "Petra", 
    "The Terracotta Army", "The Great Wall of China", "The Silk Road", "Samurai Culture", "Feudal Japan", 
    "Viking Lore", "Norse Mythology", "Runestones", "Celtic Druids", "Easter Island (Moai)",

    # --- ⚔️ DARK HISTORY & WAR ---
    "The Black Death", "The Spanish Flu", "The Dancing Plague of 1518", "The Great Fire of London", 
    "Jack the Ripper", "The Zodiac Killer", "The Mary Celeste", "The Titanic", "The Lusitania", 
    "The Hindenburg Disaster", "Chernobyl", "Fukushima", "The Cold War", "The Cuban Missile Crisis", 
    "The Berlin Wall", "Espionage Gadgets", "MK-Ultra", "Project Blue Book", "Area 51", "The Manhattan Project", 
    "Trench Warfare (WWI)", "The Christmas Truce", "The Red Baron", "Kamikaze Pilots", "The Enigma Machine", 
    "Alan Turing", "The French Revolution", "The Guillotine", "Marie Antoinette", "Napoleon Bonaparte", 
    "The Battle of Waterloo", "The American Civil War", "Abraham Lincoln", "The Salem Witch Trials", 
    "The Spanish Inquisition", "Pirates of the Caribbean", "Blackbeard", "Anne Bonny", "Torture Devices",

    # --- 🏔️ EXTREME GEOGRAPHY ---
    "Mount Everest", "The Mariana Trench", "The Dead Sea", "The Sahara Desert", "Antarctica", 
    "The Arctic Circle", "Glaciers", "Icebergs", "Volcanoes", "Supervolcanoes", "Yellowstone", 
    "Pompeii", "Krakatoa", "Tsunamis", "Earthquakes", "Tectonic Plates", "The Ring of Fire", 
    "Geysers", "Caves", "Stalactites", "Blue Holes", "Cenotes", "The Amazon River", "The Nile River", 
    "The Grand Canyon", "Uluru", "The Aurora Borealis", "The Bermuda Triangle", "Quick sand",

    # --- 🧪 WEIRD SCIENCE & PHYSICS ---
    "Quantum Mechanics", "Schrödinger's Cat", "The Double Slit Experiment", "Heisenberg Uncertainty Principle", 
    "Nuclear Fission", "Nuclear Fusion", "Radioactivity", "Marie Curie", "Nikola Tesla", "Thomas Edison", 
    "Isaac Newton", "Albert Einstein", "Darwin's Evolution", "DNA Structure", "CRISPR", "Cloning", 
    "Artificial Intelligence", "Robotics", "Nanotechnology", "Cybernetics", "Biohacking", "Cryonics", 
    "Perpetual Motion Machines", "Alchemy", "The Philosopher's Stone", "Steampunk Inventions", 
    "Leonardo da Vinci", "The Golden Ratio", "Fractals", "Chaos Theory", "The Butterfly Effect",

    # --- 🎭 OBSCURE CULTURE & MYTH ---
    "Urban Legends", "Bigfoot", "The Loch Ness Monster", "Skinwalkers", "Wendigos", "Chupacabras", 
    "The Mothman", "UFO Sightings", "Crop Circles", "Secret Societies", "The Illuminati", "The Freemasons", 
    "Skull and Bones", "Knights Templar", "The Holy Grail", "King Arthur", "Excalibur", "Greek Mythology", 
    "Roman Mythology", "Egyptian Mythology", "Norse Gods", "Yokai (Japanese Spirits)", "Djinn", 
    "Vampire Folklore", "Werewolf Folklore", "Zombie Origins", "Voodoo", "Tarot Cards", "Ouija Boards",

    # --- 🍎 EVERYDAY OBJECTS (HIDDEN HISTORIES) ---
    "The History of Coffee", "Tea Ceremonies", "Chocolate Origins", "The invention of Silk", 
    "The Printing Press", "The Telephone", "The Lightbulb", "The Internet", "Video Games", 
    "The History of Zero", "Money and Currency", "Gold Rushes", "Diamond Mining", "The Spice Trade", 
    "Glassblowing", "Blacksmithing", "Clockmaking", "Navigation Tools", "Maps and Cartography"
]

def clean_text(text):
    """Sanitizes text: removes bolding (**), bullets, dashes, quotes."""
    text = text.replace("**", "")
    text = text.replace('"', '').replace("'", "")
    return text.strip().lstrip("-•*> \"'")

def get_gemini_content():
    """Generates a Rare/Obscure Fact."""
    # 1. Pick a random topic
    chosen_topic = random.choice(TOPICS)
    print(f"✨ Topic Selected: {chosen_topic}")
    print("✨ Asking Gemini for content...")
    
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # --- PROMPT ---
    full_prompt = (
        f"ACT AS: A curator of rare, forgotten, and obscure knowledge.\n"
        f"TASK: Write one 'Iceberg Tier 3' fact about: {chosen_topic}.\n\n"

        "--- PART 1: THE FACT (Text) ---\n"
        "POSITIVE CONSTRAINTS:\n"
        "- Content: Simple, educational, and verified.\n"
        "- Style: Clear and direct sentences.\n"
        "- STRICTLY under 240 and more than 190 characters.\n"
        "NEGATIVE CONSTRAINTS:\n"
        "- NO 'Did you know' (I will add it later).\n"
        "- NO Emojis.\n"
        "- NO Dashes/Bullets.\n"
        "- NO Markdown bolding (**).\n"
        "- NO Horror, gore, or overly complex irony.\n\n"

        "--- PART 2: THE IMAGE PROMPT (Visual) ---\n"
        "Write a prompt for an AI image generator (Flux).\n"
        "Constraint: Photorealistic, award-winning wildlife photography style, no text, Cinematic lighting, 8k.\n\n"

        "FORMAT: FACT ||| IMAGE_PROMPT"
    )
    generation_config = genai.types.GenerationConfig(
        temperature=1.0 
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
                if len(fact) > 235:
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





