import redis.asyncio as redis
import os
import json
import asyncio

async def get_redis_client():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise ValueError("No REDIS_URL found.")
    
    return redis.from_url(redis_url, decode_responses=True)

# CACHE OPERATIONS FOR SPAWN LOOP
async def set_active_spawn(redis_client, channel_id: int, spawn_data: dict, ttl_seconds: int = 900):
    data_string = json.dumps(spawn_data)
    await redis_client.set(str(channel_id), data_string, ex=ttl_seconds) # stores as key: str (channel id), json: dict (data_string) pairs

async def get_active_spawn(redis_client, channel_id: int) -> dict:
    data_string = await redis_client.get(str(channel_id))

    if data_string:
        return json.loads(data_string)
    
    return {}

async def delete_active_spawn(redis_client, channel_id: int):
    await redis_client.delete(str(channel_id))

# script for testing the redis db connection
async def test_connection():
    from dotenv import load_dotenv
    load_dotenv()

    print("Attempting to connect to Redis...")
    try:
        client = await get_redis_client()
        
        # Ping the server to ensure connection is alive
        await client.ping()
        print("✅ SUCCESS! Connected to Redis.")
        
        # Test our functions
        test_channel = 123456789
        test_data = {"name": "Pikachu", "id": 25, "is_shiny": False}
        
        print("Testing Write/Read...")
        await set_active_spawn(client, test_channel, test_data, ttl_seconds=10)
        retrieved = await get_active_spawn(client, test_channel)
        print(f"Retrieved: {retrieved['name']}")
        
        print("Testing Delete...")
        await delete_active_spawn(client, test_channel)
        
        await client.close()
    except Exception as e:
        print(f"\n❌ FAILED to connect: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())