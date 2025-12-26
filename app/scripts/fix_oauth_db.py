import asyncio

from sqlalchemy import text

from app.database.connection import engine


async def fix_schema():
    async with engine.begin() as conn:
        await conn.execute(
            text("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL")
        )
        print("✓ Schema updated: hashed_password now allows NULL for OAuth users")


if __name__ == "__main__":
    asyncio.run(fix_schema())
