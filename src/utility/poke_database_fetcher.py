import requests
import json
import time

# def generate_pokemon_database():
#     # The limit=1025 ensures we get all current Pokemon in one single request
#     url = "https://pokeapi.co/api/v2/pokemon?limit=1025"
#     print("Fetching data from PokeAPI...")
    
#     response = requests.get(url)
#     data = response.json()

#     # Create a dictionary mapping the ID to the Pokemon's name
#     pokemon_dict = {}
    
#     # We will loop through the results and extract the true ID from the URL string.
#     for entry in data['results']:
#         # The url looks like: "https://pokeapi.co/api/v2/pokemon/1/"
#         # We can strip the trailing slash, split it by '/', and grab the very last item.
#         url_parts = entry['url'].strip('/').split('/')
#         pokemon_id = url_parts[-1] 
        
#         pokemon_dict[pokemon_id] = entry['name']

#     # Save this dictionary to a local file
#     with open('pokemon_data.json', 'w') as f:
#         json.dump(pokemon_dict, f, indent=4)
    
#     print("Successfully saved 1025 Pokémon to pokemon_data.json!")

def generate_advanced_database():
    pokemon_db = {}
    print("Fetching 1025 Pokémon species data... (This will take about 2 minutes)")

    # Loop through all 1025 base Pokemon
    for i in range(1, 1026):
        url = f"https://pokeapi.co/api/v2/pokemon-species/{i}/"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # 1. Grab the name
            name = data['name']
            
            # 2. Grab the capture rate (3 to 255). We will use this as the spawn weight!
            # If a capture rate is missing for some reason, default to 45 (average).
            capture_rate = data.get('capture_rate', 45)
            
            # 3. Check if it's Legendary or Mythical
            is_legendary = data.get('is_legendary', False)
            is_mythical = data.get('is_mythical', False)
            
            # Force legendary/mythical spawn weights to be EXTREMELY low
            # even if their capture rate is weirdly high.
            if is_legendary or is_mythical:
                spawn_weight = 1  # Super rare!
            else:
                spawn_weight = capture_rate # Common pokemon (255) spawn 255x more often than legendaries (1)
            
            # Save it to our dictionary
            pokemon_db[str(i)] = {
                "name": name,
                "weight": spawn_weight,
                "is_rare": is_legendary or is_mythical
            }
            
            # Print progress every 100 Pokemon
            if i % 100 == 0:
                print(f"Processed {i}/1025...")
                
        # Sleep for a tiny bit so PokéAPI doesn't ban our IP address for spamming
        time.sleep(0.1) 

    # Save to JSON
    with open('advanced_pokemon_data.json', 'w') as f:
        json.dump(pokemon_db, f, indent=4)
        
    print("Successfully built the advanced rarity database!")

if __name__ == "__main__":
    generate_advanced_database()