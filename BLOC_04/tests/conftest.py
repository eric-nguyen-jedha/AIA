import sys
from unittest.mock import MagicMock
import pytest


# 🛡️ Mock des modules Airflow pour permettre l'import hors environnement Airflow
# (ex: dans Jenkins, où apache-airflow n'est pas installé)
_airflow_modules = [
    "airflow",
    "airflow.models",
    "airflow.models.Variable",
    "airflow.exceptions",
    "airflow.providers",
    "airflow.providers.amazon",
    "airflow.providers.amazon.aws",
    "airflow.providers.amazon.aws.hooks",
    "airflow.providers.amazon.aws.hooks.s3",
]

for mod_name in _airflow_modules:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()


# 🧪 Fixture utilitaire pour les tests
@pytest.fixture
def mock_ti():
    """Fixture pour mocker le TaskInstance (XCom)."""
    ti = MagicMock()
    yield ti
