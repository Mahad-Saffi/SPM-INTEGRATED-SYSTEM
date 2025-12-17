from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.config.database import SessionLocal

class UserService:
    async def get_all_users(self) -> list[User]:
        async with SessionLocal() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            return users

user_service = UserService()
