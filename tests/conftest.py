from collections.abc import Generator
from httpx import Headers
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import StaticPool

from src.core.database import Base, get_db
from src.core.security import hash_password
from src.main import app
from src.models.role import Role
from src.models.permission import Permission
from src.models.user import User
from src.init_db import INIT_AUTH_DATA

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=StaticPool)
TestSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


async def db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = db


@pytest.fixture(scope="function", autouse=True)
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        permissions = []
        for permission in INIT_AUTH_DATA["permissions"]:
            _permission = Permission(
                name=permission["name"], description=permission["description"]
            )
            permissions.append(_permission)
        session.add_all(permissions)

        roles = []
        for role in INIT_AUTH_DATA["roles"]:
            _role = Role(
                name=role["name"],
                description=role["description"],
                permissions=[
                    permission
                    for idx, permission in enumerate(permissions, 1)
                    if idx in role["permissions"]
                ],
            )
            roles.append(_role)
        session.add_all(roles)

        users = []
        for user in INIT_AUTH_DATA["users"]:
            _user = User(
                name=user["name"],
                email=user["email"],
                password=hash_password(user["password"]),
                roles=[
                    role for idx, role in enumerate(roles, 1) if idx in user["roles"]
                ],
            )
            users.append(_user)
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
def admin_authenticated(client: TestClient):
    rs = client.post(
        "auth/token",
        data={"username": "admin@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()

    client.headers = Headers({"Authorization": f"Bearer {rs['access_token']}"})

    return client


@pytest.fixture
def standard_authenticated(client: TestClient):
    rs = client.post(
        "auth/token",
        data={"username": "standard@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()

    client.headers = Headers({"Authorization": f"Bearer {rs['access_token']}"})

    return client
