import json

# Each tier gets a fixed share of TOTAL spawn probability, split evenly across
# however many species happen to land in it. This is the fix for the old
# scheme (spawn_weight = raw capture_rate): capture_rate clusters heavily
# around a handful of default values (e.g. 294 species share capture_rate 45),
# so a big tier ended up with more combined spawn odds than rarer, less
# populated tiers with individually higher weights. Splitting probability
# per-tier instead of per-raw-value makes tier population irrelevant.
#
# Legendaries, mythicals, and ultra beasts are lumped into one "special" tier
# so every species in that group gets the exact same (very low) weight,
# regardless of which of the three flags it carries.
TIER_PROBABILITY = {
    "common": 0.55,
    "uncommon": 0.30,
    "rare": 0.145,
    "special": 0.005,  # legendary + mythical + ultra_beast, combined
}

SCALE = 100_000  # resolution for converting probability share into integer weights


def classify(poke_info):
    if poke_info.get("is_ultra_beast") or poke_info.get("is_mythical") or poke_info.get("is_legendary"):
        return "special"

    # For everyone else, spawn_weight still holds the raw PokeAPI capture_rate
    # value from the fetcher. Bucket it into a rarity tier.
    capture_rate = poke_info["spawn_weight"]
    if capture_rate >= 150:
        return "common"
    elif capture_rate >= 75:
        return "uncommon"
    else:
        return "rare"


def rarity_label(poke_info):
    if poke_info.get("is_ultra_beast"):
        return "ultra_beast"
    if poke_info.get("is_mythical"):
        return "mythical"
    if poke_info.get("is_legendary"):
        return "legendary"
    return None


def rebalance():
    filename = "./ultimate_pokemon_data.json"

    print(f"Loading {filename}...")
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    # First pass: classify everyone and count tier populations
    tier_of = {}
    tier_counts = {tier: 0 for tier in TIER_PROBABILITY}
    for poke_id, poke_info in data.items():
        tier = classify(poke_info)
        tier_of[poke_id] = tier
        tier_counts[tier] += 1

    print("Tier populations:", tier_counts)

    # Second pass: assign final weight = (tier's total probability / tier size).
    # rarity_tier keeps the specific label (legendary/mythical/ultra_beast) for
    # display purposes even though weight comes from the merged "special" tier.
    for poke_id, poke_info in data.items():
        tier = tier_of[poke_id]
        count = tier_counts[tier]
        weight = round((TIER_PROBABILITY[tier] / count) * SCALE)
        poke_info["spawn_weight"] = max(1, weight)
        poke_info["rarity_tier"] = rarity_label(poke_info) or tier

    print("Saving changes...")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print("Done! spawn_weight now reflects fixed per-tier spawn odds.")


if __name__ == "__main__":
    rebalance()
