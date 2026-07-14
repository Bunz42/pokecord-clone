import requests
import json
import time

def get_english_flavor_text(entries):
    """Finds the first English pokedex entry and cleans up weird API linebreaks."""
    for entry in entries:
        if entry['language']['name'] == 'en':
            # PokéAPI leaves weird \n and \f characters in their text. This removes them.
            return entry['flavor_text'].replace('\n', ' ').replace('\f', ' ')
    return "No Pokédex description available."

def build_ultimate_database():
    master_db = {}
    print("Fetching the Ultimate Pokémon Database...")
    print("Go grab a coffee, this will take about 10-12 minutes to respect API rate limits.")

    # Fetch up to 1025 (End of Gen 9)
    for i in range(1, 1026):
        try:
            # 1. Species Data (The Core Entity)
            species_res = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{i}/").json()
            
            name = species_res['name']
            is_legendary = species_res.get('is_legendary', False)
            is_mythical = species_res.get('is_mythical', False)
            capture_rate = species_res.get('capture_rate', 45)
            flavor_text = get_english_flavor_text(species_res.get('flavor_text_entries', []))
            
            # Provisional spawn weight only - run ultra_beast_json_patcher.py then
            # rebalance_spawn_weights.py after this to get final, tier-normalized weights.
            if is_legendary or is_mythical:
                spawn_weight = 1 # Make them incredibly rare
            else:
                spawn_weight = capture_rate # Common pokemon spawn more often (up to 255 weight)
            
            # Save the evolution chain URL for the bot to use later
            evo_chain_url = None
            if species_res.get('evolution_chain'):
                evo_chain_url = species_res['evolution_chain']['url']
            
            master_db[str(i)] = {
                "name": name,
                "is_legendary": is_legendary,
                "is_mythical": is_mythical,
                "spawn_weight": spawn_weight,
                "description": flavor_text,
                "evolution_chain_url": evo_chain_url,
                "forms": {}
            }
            
            # 2. Loop through ALL varieties (Base form + Alternate forms)
            for variety in species_res['varieties']:
                form_name = variety['pokemon']['name']
                form_url = variety['pokemon']['url']
                is_default = variety['is_default']
                
                # Fetch the specific stats for this form
                form_res = requests.get(form_url).json()
                
                # Parse Stats & Types
                parsed_stats = {stat['stat']['name']: stat['base_stat'] for stat in form_res['stats']}
                types = [t['type']['name'] for t in form_res['types']]
                valid_moves = [move['move']['name'] for move in form_res['moves']]
                
                # PokéAPI returns height in decimetres and weight in hectograms. 
                # We convert them to standard meters and kg.
                height_m = form_res.get('height', 0) / 10  
                weight_kg = form_res.get('weight', 0) / 10 
                
                form_data = {
                    "types": types,
                    "height_m": height_m,
                    "weight_kg": weight_kg,
                    "base_stats": parsed_stats,
                    "valid_moves": valid_moves
                }
                
                if is_default:
                    master_db[str(i)]["forms"]["base"] = form_data
                else:
                    # Clean up form name (e.g., 'venusaur-mega' -> 'mega')
                    clean_form_name = form_name.replace(f"{name}-", "")
                    master_db[str(i)]["forms"][clean_form_name] = form_data

            if i % 25 == 0:
                print(f"Processed {i}/1025 ({name.title()})...")
                
            time.sleep(0.2) # Rate limit protection

        except Exception as e:
            print(f"Error fetching data for ID {i}: {e}")

    # Save to file with UTF-8 encoding for special characters
    with open('ultimate_pokemon_data.json', 'w', encoding='utf-8') as f:
        json.dump(master_db, f, indent=4, ensure_ascii=False)
        
    print("Successfully built ultimate_pokemon_data.json! You never have to do this again.")

if __name__ == "__main__":
    build_ultimate_database()