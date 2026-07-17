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
        # NOTE: players and caught_pokemon reference each other (circular FK), so
        # players is created without the active_pokemon_id FK first; the constraint
        # is added after caught_pokemon exists (see ALTER TABLE below).
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS players (
                discord_id bigint primary key,
                balance integer default 0,
                last_daily timestamp,
                active_pokemon_id INTEGER
            )
        ''')

        # TODO: need to fetch species ids and nature from pokeapi so table insertions don't fail (add NOT NULL back to species_id)
        # TODO: need to add a Moves dictionary for each move slot and link the moves as a foreign key to that. Similarly, need an Items dict for foreign key held_item_id.
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS caught_pokemon (
                id serial primary key,
                owner_id bigint references players(discord_id),
                original_owner_id bigint references players(discord_id),
                species_id int,
                form varchar default 'base',
                nickname varchar(32),
                level int default 1 CHECK (level BETWEEN 1 AND 100),
                xp int default 0,
                is_legendary boolean default false,
                is_mythical boolean default false,
                is_ultra_beast boolean default false,
                is_shiny boolean default false,
                nature VARCHAR(20) NOT NULL default 'docile',
                iv_hp smallint CONSTRAINT chk_iv_hp CHECK (iv_hp BETWEEN 0 AND 31),
                iv_atk smallint CONSTRAINT chk_iv_atk CHECK (iv_atk BETWEEN 0 AND 31),
                iv_def smallint CONSTRAINT chk_iv_def CHECK (iv_def BETWEEN 0 AND 31),
                iv_spatk smallint CONSTRAINT chk_iv_spatk CHECK (iv_spatk BETWEEN 0 AND 31),
                iv_spdef smallint CONSTRAINT chk_iv_spdef CHECK (iv_spdef BETWEEN 0 AND 31),
                iv_speed smallint CONSTRAINT chk_iv_speed CHECK (iv_speed BETWEEN 0 AND 31),
                total_iv_percent NUMERIC(5, 2) GENERATED ALWAYS AS (
                    ROUND (
                        ((iv_hp + iv_atk + iv_def + iv_spatk + iv_spdef + iv_speed)::NUMERIC / 186.0) * 100.0,
                        2
                    )
                ) STORED,
                move_1 int,     
                move_2 int,     
                move_3 int,     
                move_4 int, 
                held_item_id int,
                is_favorite boolean default false,
                caught_at timestamp default current_timestamp
            )
        ''')

        # now that caught_pokemon exists, add the FK on players.active_pokemon_id.
        # guarded so re-running setup_tables doesn't error on a duplicate constraint.
        await conn.execute('''
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'fk_active_pokemon'
                ) THEN
                    ALTER TABLE players
                        ADD CONSTRAINT fk_active_pokemon
                        FOREIGN KEY (active_pokemon_id) REFERENCES caught_pokemon(id);
                END IF;
            END $$;
        ''')

        print("Tables created succesfully!")
        print("--------")

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