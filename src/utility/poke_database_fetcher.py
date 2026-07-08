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

def build_pokemon_data():
    pokemon_db = {}
    print("Fetching Pokémon species data... (This will take a few minutes...)")

    # Loop through all 1025 base Pokemon
    for i in range(1, 1026):
        species_response = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{i}/").json()
        base_response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{i}/").json()
        
        parsed_stats = {stat['stat']['name']: stat['base_stat'] for stat in base_response['stats']}
    
        # Parse Move Pool
        # We just want a list of move names this pokemon can legally learn
        valid_moves = [move['move']['name'] for move in base_response['moves']]
        
        # Parse Types
        types = [t['type']['name'] for t in base_response['types']]

        # Merge it all together
        pokemon_db[str(i)] = {
            "name": base_response['name'],
            "is_rare": species_response.get('is_legendary', False) or species_response.get('is_mythical', False),
            "capture_rate": species_response.get('capture_rate', 45),
            "types": types,
            "base_stats": parsed_stats,
            "valid_moves": valid_moves
        }
        
        if i % 50 == 0:
            print(f"Processed {i}/1025...")
        time.sleep(0.2) # Be nice to PokeAPI!

    with open('master_pokemon_data.json', 'w') as f:
        json.dump(pokemon_db, f, indent=4)
        
    print("Master database built successfully!")

if __name__ == "__main__":
    build_pokemon_data()