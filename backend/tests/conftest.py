import os

os.environ["RATE_LIMIT_ENABLED"] = "false"

from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime
from httpx import Headers
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy import StaticPool

from src.core.database import Base, get_db
from src.core.security import hash_secret
from src.enums import PERMISSION_DESCRIPTIONS
from src.enums import Permission as PermissionEnum
from src.main import app
from src.models.tenant import Tenant
from src.models.role import Role
from src.models.permission import Permission
from src.models.user import User
from src.models.user_tenant import UserTenant
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
        tenants = []
        for tenant in INIT_AUTH_DATA["tenants"]:
            tenants.append(Tenant(name=tenant["name"]))
        session.add_all(tenants)

        permissions = []
        for permission in PermissionEnum:
            permissions.append(
                Permission(
                    name=permission.value,
                    description=PERMISSION_DESCRIPTIONS[permission],
                )
            )
        session.add_all(permissions)

        roles = []
        for role in INIT_AUTH_DATA["roles"]:
            roles.append(
                Role(
                    name=role["name"],
                    description=role["description"],
                    tenant=tenants[role["tenant"] - 1],
                    permissions=[
                        permission
                        for permission in permissions
                        if permission.name in role["permissions"]
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
                    password=hash_secret(user["password"]),
                    roles=[
                        role
                        for idx, role in enumerate(roles, 1)
                        if idx in user["roles"]
                    ],
                )
            )
        session.add_all(users)

        await session.flush()

        user_tenants = []
        for user_data, user in zip(INIT_AUTH_DATA["users"], users):
            user_tenants.append(
                UserTenant(
                    user_id=user.id,
                    tenant_id=tenants[user_data["tenant"] - 1].id,
                    last_active_at=datetime.now(UTC),
                )
            )
        session.add_all(user_tenants)

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
        "/v1/auth/token",
        data={"username": "admin@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()

    client.headers = Headers({"Authorization": f"Bearer {rs['access_token']}"})

    return client


@pytest.fixture
def standard_authenticated(client: TestClient) -> TestClient:
    rs = client.post(
        "/v1/auth/token",
        data={"username": "standard@example.org", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()

    client.headers = Headers({"Authorization": f"Bearer {rs['access_token']}"})

    return client


@pytest.fixture
def tenant2_admin_authenticated() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        rs = c.post(
            "/v1/auth/token",
            data={"username": "admin2@example.org", "password": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ).json()

        c.headers = Headers({"Authorization": f"Bearer {rs['access_token']}"})

        yield c
