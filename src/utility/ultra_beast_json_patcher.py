import json

def patch_json_data():
    filename = './ultimate_pokemon_data.json'
    
    # Hardcoded set of Ultra Beasts for blazing fast lookups
    ULTRA_BEASTS = {
        "nihilego", "buzzwole", "pheromosa", "xurkitree", 
        "celesteela", "kartana", "guzzlord", "poipole", 
        "naganadel", "stakataka", "blacephalon"
    }

    print(f"Loading {filename}...")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {filename}. Make sure it is in the same folder.")
        return

    print("Patching Ultra Beast data...")
    ub_count = 0

    # Loop through the dictionary and update the fields
    for poke_id, poke_info in data.items():
        name = poke_info.get("name", "")
        is_ub = name.lower() in ULTRA_BEASTS
        
        # Add the new ultra beast flag
        poke_info["is_ultra_beast"] = is_ub
        
        # If it is an Ultra Beast, override its rarity and spawn weight
        if is_ub:
            poke_info["spawn_weight"] = 1
            ub_count += 1

    print(f"Successfully identified and updated {ub_count} Ultra Beasts.")

    # Save the modified dictionary back into the same JSON file
    print("Saving changes...")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    print("Done! Your database is now patched and ready to go.")

if __name__ == "__main__":
    patch_json_data()