import streamlit as st
import requests
import json
import os
from pathlib import Path
from supabase import create_client, Client



script_dir = Path(__file__).parent
# All Card Data

giturl = str(script_dir / "cards.json")


# Cache the data
@st.cache_data
def load_master_cards(url):
    with open(url, "r", encoding="utf-8") as file:
        data = json.load(file)
    # response = requests.get(url)
    return data

# Load Cards
try:
    ALL_CARDS = load_master_cards(giturl)
except Exception as e:
    st.error("Failed to load card info from git")
    ALL_CARDS = {}

RARITY_ORDER = {
    "Limited Edition": 0,
    "Legendary": 1,
    "Epic": 2,
    "Rare": 3,
    "Uncommon": 4,
    "Common": 5
}

# 2. Build the CSS styles (Notice the new '.binder-row' class to align them)
html_content = """
<style>
.binder-row {
  display: flex;
  flex-wrap: wrap;         /* Allows cards to wrap to the next line if the screen is too small */
  gap: 20px;               /* Space between your cards */
  justify-content: center; /* Centers the row of cards on the page */
  padding: 20px;
}

.flip-card {
  background-color: transparent;
  width: 200px;            /* Slimmed down slightly to fit a row better */
  height: 280px;
  perspective: 1000px;
}

.flip-card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  text-align: center;
  transition: transform 0.6s;
  transform-style: preserve-3d;
}

.flip-card:hover .flip-card-inner {
  transform: rotateY(180deg);
}

.flip-card-front, .flip-card-back {
  position: absolute;
  width: 100%;
  height: 100%;
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
}

.flip-card-front img, .flip-card-back img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

.flip-card-back {
  transform: rotateY(180deg);
}


/* 1. Hide the tracking checkbox completely */
.card-trigger {
  display: none;
}

/* FIX: Force the label container to behave like a standard grid block item */
.card-container {
  display: block; 
  cursor: pointer;
  width: 200px;  /* Matches your card width exactly */
  height: 280px; /* Matches your card height exactly */
  position: relative;
}

/* FORCE ENTIRE PARENT WRAPPER TO THE ABSOLUTE FOREGROUND WHEN CHECKED */
.card-trigger:checked + .card-container {
  position: relative;
  z-index: 999999; /* Higher than all other cards combined */
}

/* 3. The Backdrop overlay - FIXED to fill the screen */
.card-container::before {
  content: "";
  position: fixed;
  
  /* Force positioning relative to the screen viewport, not the card slot */
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  
  background: rgba(0, 0, 0, 0.85); 
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.3s ease;
  z-index: 99999; 
}

/* 4. Activate the backdrop overlay */
.card-trigger:checked + .card-container::before {
  opacity: 1;
  visibility: visible;
}

/* 5. FIX: Absolute viewport targeting to force perfect centering */
.card-trigger:checked + .card-container .flip-card {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  margin: auto; /* Magic trick: combined with fixed 0 coordinates, this centers perfectly */
  width: 300px;  /* Blown up size dimensions */
  height: 420px;
  transform: scale(1.3); 
  z-index: 100000;
  box-shadow: 0 20px 50px rgba(0,0,0,0.8);
}

.flip-card {
  transition: transform 0.4s ease, box-shadow 0.4s ease, width 0.4s ease, height 0.4s ease;
}

</style>

<div class="binder-row">
"""


# 3. Initialize Supabase
url: str = os.environ.get("SUPABASE_RIGHT")
key: str = os.environ.get("SUPABASE_CARDS")
supabase: Client = create_client(url, key)

st.title("🎴 Digital Card Binder")

# 2 Authenticate User
username = st.text_input("Enter Twitch Username").lower().strip()

if username:
    try:
        response = (
            supabase.table("users")
          .select("id, name, user_cards(Amount, cards(id, name, rarity, pack, card_num))")
          .eq("name", username)
          .execute()
        )

        if response.data:
            user_data = response.data[0]
            st.success(f"Found binder for {user_data['name']}!")

            raw_inventory = user_data.get("user_cards", [])

            if raw_inventory:
                st.markdown("### Your Collection:")

                user_inventory = []
                for item in raw_inventory:
                    card_info = item["cards"]
                    user_inventory.append({
                        "card_id": card_info["id"],
                        "name": card_info["name"],
                        "rarity": card_info["rarity"],
                        "num": card_info["card_num"],
                        "amount": item["Amount"]
                    })

                sort_option = st.selectbox(
                    "Sort Binder By:",
                    options=["Default (Release Order)","Rarity (High to Low)", "Rarity (Low to High)"]
                )

                user_inventory.sort(key=lambda x: x["num"])

                if sort_option == "Rarity (High to Low)":
                    user_inventory.sort(key=lambda x:RARITY_ORDER.get(x["rarity"], 99))

                elif sort_option == "Rarity (Low to High)":
                    user_inventory.sort(key=lambda x:RARITY_ORDER.get(x["rarity"], 99), reverse=True)

                for card in user_inventory:
                    cid = str(card['card_id'])

                    if cid in ALL_CARDS:
                        html_content += f"""
<input type="checkbox" id="zoom-{cid}" class="card-trigger">
<label for="zoom-{cid}" class="card-container">                        
<div class="flip-card">
<div class="flip-card-inner">
<div class="flip-card-front">
<img src="{ALL_CARDS[cid]['front']}" alt="Card {ALL_CARDS[cid]['name']} Front">
</div>
<div class="flip-card-back">
<img src="{ALL_CARDS[cid]['back']}" alt="Card {ALL_CARDS[cid]['name']} Back">
</div>
</div>
</div>
</label>
"""

                # 4. Close the binder-row div
                html_content += "</div>"

                # 5. Render everything with a single Streamlit call
                st.markdown(html_content, unsafe_allow_html=True)
            else:
                st.info("You don't own any cards yet!")
        else:
            st.error(f"User {username} not found in database")
    except Exception as e:
        st.error(f"An error occured while fetching data: {e}")


# # Injecting the 3D flipping styling
# st.markdown(
#     """
