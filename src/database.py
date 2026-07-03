import asyncpg
import asyncio
import os

async def create_db_pool(): # pool is better than regular conn for pokecord since it handles many requests for short connection times per request
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("make sure your database url is in your env file")
    
    return await asyncpg.create_pool(database_url)

async def setup_tables(pool):
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS players (
                discord_id bigint primary key,
                name text,
                balance integer default 0,
                last_daily timestamp
            )
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS caught_pokemon (
                id serial primary key,
                owner_id bigint references players(discord_id),
                species_id integer,
                is_shiny boolean,
                caught_at timestamp default current_timestamp
            )
        ''')
        print("Tables verified/created succesfully!")

async def test_connection():
    from dotenv import load_dotenv
    load_dotenv()

    print("Attempting to connect to supabase...")
    try:
        pool = await create_db_pool()
        await setup_tables(pool)

        print("Successfully connected to supabase!")
        await pool.close()
    except Exception as e:
        print(f"Failed to connect with exception {e}")
        print("Check your DATABASE_URL in the .env file and ensure your password is correct.")

if __name__ == "__main__":
    # This block only runs if you execute this file directly
    asyncio.run(test_connection())