from collections.abc import AsyncGenerator, Generator
from httpx import Headers
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy import StaticPool

from src.core.database import Base, get_db
from src.core.security import hash_password
from src.main import app
from src.models.company import Company
from src.models.role import Role
from src.models.permission import Permission
from src.models.user import User
from src.init_db import INIT_AUTH_DATA

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=StaticPool)
TestSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


async def db() -> AsyncGenerator[AsyncSession]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = db


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator[None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        companies = []
        for company in INIT_AUTH_DATA["companies"]:
            companies.append(Company(name=company["name"]))
        session.add_all(companies)

        permissions = []
        for permission in INIT_AUTH_DATA["permissions"]:
            permissions.append(
                Permission(
                    name=permission["name"], description=permission["description"]
                )
            )
        session.add_all(permissions)

        roles = []
        for role in INIT_AUTH_DATA["roles"]:
            roles.append(
                Role(
                    name=role["name"],
                    description=role["description"],
                    permissions=[
                        permission
                        for idx, permission in enumerate(permissions, 1)
                        if idx in role["permissions"]
                    ],
                )
            )
        session.add_all(roles)

        users = []
        for user in INIT_AUTH_DATA["users"]:
            users.append(
                User(
                    name=user["name"],
                    email=user["email"],
                    password=hash_password(user["password"]),
                    company=companies[user["company"] - 1],
                    roles=[
                        role
                        for idx, role in enumerate(roles, 1)
                        if idx in user["roles"]
                    ],
                )
            )
        session.add_all(users)

        await session.commit()
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(name="client")
def _client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_authenticated(client: TestClient) -> TestClient:
    rs = client.post(
        "auth/token",
        data={"username": "admin@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()

    client.headers = Headers({"Authorization": f"Bearer {rs['access_token']}"})

    return client


@pytest.fixture
def standard_authenticated(client: TestClient) -> TestClient:
    rs = client.post(
        "auth/token",
        data={"username": "standard@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()

    client.headers = Headers({"Authorization": f"Bearer {rs['access_token']}"})

    return client
