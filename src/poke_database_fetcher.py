import requests
import json

def generate_pokemon_database():
    # The limit=1025 ensures we get all current Pokemon in one single request
    url = "https://pokeapi.co/api/v2/pokemon?limit=1025"
    print("Fetching data from PokeAPI...")
    
    response = requests.get(url)
    data = response.json()

    # Create a dictionary mapping the ID to the Pokemon's name
    pokemon_dict = {}
    
    # We will loop through the results and extract the true ID from the URL string.
    for entry in data['results']:
        # The url looks like: "https://pokeapi.co/api/v2/pokemon/1/"
        # We can strip the trailing slash, split it by '/', and grab the very last item.
        url_parts = entry['url'].strip('/').split('/')
        pokemon_id = url_parts[-1] 
        
        pokemon_dict[pokemon_id] = entry['name']

    # Save this dictionary to a local file
    with open('pokemon_data.json', 'w') as f:
        json.dump(pokemon_dict, f, indent=4)
    
    print("Successfully saved 1025 Pokémon to pokemon_data.json!")

if __name__ == "__main__":
    generate_pokemon_database()