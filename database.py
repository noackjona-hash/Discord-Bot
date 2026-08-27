import os
import aiosqlite
import logging

logger = logging.getLogger("Database")
DB_PATH = os.path.join(os.path.dirname(__file__), "smp_data.db")

async def init_db():
    """Initializes SQLite database and tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Settings table (guild configs, server IP, rcon details, etc.)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                server_ip TEXT,
                server_port INTEGER DEFAULT 25565,
                rcon_port INTEGER DEFAULT 25575,
                rcon_password TEXT,
                live_channel_id INTEGER,
                live_message_id INTEGER,
                whitelist_channel_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # SMP Waypoints / Coordinates table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS waypoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                dimension TEXT NOT NULL DEFAULT 'Overworld',
                x INTEGER NOT NULL,
                y INTEGER,
                z INTEGER NOT NULL,
                description TEXT,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # SMP Marketplace / Shops table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS shops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                owner_id INTEGER NOT NULL,
                owner_name TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                price TEXT NOT NULL,
                location TEXT NOT NULL,
                in_stock BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Whitelist Applications
        await db.execute("""
            CREATE TABLE IF NOT EXISTS whitelist_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                minecraft_name TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()
    logger.info("SQLite Database initialized successfully.")

async def get_guild_setting(guild_id: int, key: str, default=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(f"SELECT {key} FROM guild_settings WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[key] is not None:
                return row[key]
    return default

async def set_guild_setting(guild_id: int, key: str, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"""
            INSERT INTO guild_settings (guild_id, {key})
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET {key} = ?
        """, (guild_id, value, value))
        await db.commit()
