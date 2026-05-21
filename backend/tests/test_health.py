"""Test santé minimal pour la CI."""


def test_health():
    """Le module se charge sans erreur."""
    from app.config import settings
    assert settings.APP_NAME
