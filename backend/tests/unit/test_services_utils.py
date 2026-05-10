# mypy: disable-error-code="no-untyped-def"

"""Unit tests for src/services/utils.py - setup_new_organization and send_email."""

from unittest.mock import MagicMock

from src.repositories.repository_manager import RepositoryManager
from src.services.utils import send_email, setup_new_organization
from tests.conftest import TestSessionLocal

# ---------------------------------------------------------------------------
# setup_new_organization
# ---------------------------------------------------------------------------


async def test_setup_new_organization_creates_roles_and_subscription():
    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)

            # Create a fresh org + user
            org = await repos.organization.create(name="Fresh Org")
            user = await repos.user.create(
                name="Fresh User",
                email="fresh@example.com",
                password="hashed",
                terms_accepted_at=None,
            )

            await setup_new_organization(repos, org, user)

            # After setup: Owner role should exist for this org
            roles = await repos.role.get_all()
            org_roles = [r for r in roles if r.organization_id == org.id]
            assert any(r.is_protected for r in org_roles), (
                "Owner role should be created"
            )

            # A subscription should have been created for the org
            sub = await repos.subscription.get_active_for_organization(org.id)
            assert sub is not None
            assert sub.status == "active"


async def test_setup_new_organization_no_free_plan_logs_warning(caplog):
    """
    When no free price exists, setup_new_organization
    logs a warning and skips sub creation.
    """
    import logging

    async with TestSessionLocal() as session:
        async with session.begin():
            repos = RepositoryManager(session)

            # Remove the free price by deactivating it
            prices = await repos.plan_price.get_all()
            for price in prices:
                if price.amount == 0:
                    await repos.plan_price.update(price, is_active=False)

            org = await repos.organization.create(name="No Free Plan Org")
            user = await repos.user.create(
                name="Nofree User",
                email="nofree@example.com",
                password="hashed",
                terms_accepted_at=None,
            )

            with caplog.at_level(logging.WARNING, logger="src.services.utils"):
                await setup_new_organization(repos, org, user)

            assert any("free plan" in r.message.lower() for r in caplog.records)

            # No subscription created for this org
            sub = await repos.subscription.get_active_for_organization(org.id)
            assert sub is None


# ---------------------------------------------------------------------------
# send_email
# ---------------------------------------------------------------------------


def test_send_email_calls_smtp(mocker):  # type: ignore[no-untyped-def]
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)
    mock_smtp_instance.has_extn.return_value = False

    mocker.patch("src.services.utils.SMTP", return_value=mock_smtp_instance)

    send_email(
        address="user@example.com",
        user_name="Test User",
        subject="Hello",
        email_template="verify-email",
        data={
            "verify_url": "https://app.example.com/verify?token=abc",
            "expiration_hours": 24,
        },
    )

    mock_smtp_instance.send_message.assert_called_once()


def test_send_email_smtp_failure_is_silent(mocker):  # type: ignore[no-untyped-def]
    """SMTP errors must not propagate - they are logged and swallowed."""
    mocker.patch(
        "src.services.utils.SMTP", side_effect=ConnectionRefusedError("refused")
    )

    # Should not raise
    send_email(
        address="user@example.com",
        user_name="User",
        subject="Test",
        email_template="verify-email",
        data={"verify_url": "https://x.com/verify", "expiration_hours": 1},
    )


def test_send_email_no_data_uses_defaults(mocker):  # type: ignore[no-untyped-def]
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)
    mock_smtp_instance.has_extn.return_value = False

    mocker.patch("src.services.utils.SMTP", return_value=mock_smtp_instance)

    send_email(
        address="user@example.com",
        user_name="User",
        email_template="welcome",
        data={"login_url": "https://app.com/login"},
    )

    mock_smtp_instance.send_message.assert_called_once()


def test_send_email_with_none_data(mocker):  # type: ignore[no-untyped-def]
    """data=None triggers the `data = {}` branch (line 71)."""
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)
    mock_smtp_instance.has_extn.return_value = False

    mocker.patch("src.services.utils.SMTP", return_value=mock_smtp_instance)

    send_email(
        address="user@example.com",
        user_name="User",
        subject="Hello",
        email_template="verify-email",
        data=None,
    )

    mock_smtp_instance.send_message.assert_called_once()


def test_send_email_with_starttls(mocker):  # type: ignore[no-untyped-def]
    """
    email_tls=True (default) + has_extn truthy > starttls() and second ehlo() called.
    """
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)
    # has_extn returns a truthy MagicMock by default - STARTTLS path is taken
    mock_smtp_instance.has_extn.return_value = True

    mocker.patch("src.services.utils.SMTP", return_value=mock_smtp_instance)
    # Patch only email_tls so the rest of settings keeps real string values
    mocker.patch("src.services.utils.settings.email_tls", True)

    send_email(
        address="user@example.com",
        user_name="User",
        subject="Hello",
        email_template="verify-email",
        data={"verify_url": "https://x.com/v", "expiration_hours": 1},
    )

    mock_smtp_instance.starttls.assert_called_once()
    assert mock_smtp_instance.ehlo.call_count == 2


def test_send_email_with_smtp_credentials(mocker):  # type: ignore[no-untyped-def]
    """Non-empty email_user + email_password > smtp.login() is called."""
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)
    mock_smtp_instance.has_extn.return_value = False

    mocker.patch("src.services.utils.SMTP", return_value=mock_smtp_instance)
    mock_settings = mocker.patch("src.services.utils.settings")
    mock_settings.email_tls = False
    mock_settings.email_user = "smtp_user"
    mock_settings.email_password = "smtp_pass"
    mock_settings.app_name = "TestApp"
    mock_settings.email_from_address = "noreply@example.com"
    mock_settings.email_from_name = "TestApp"
    mock_settings.email_host = "localhost"
    mock_settings.email_port = 587

    send_email(
        address="user@example.com",
        user_name="User",
        subject="Hello",
        email_template="verify-email",
        data={"verify_url": "https://x.com/v", "expiration_hours": 1},
    )

    mock_smtp_instance.login.assert_called_once_with("smtp_user", "smtp_pass")
