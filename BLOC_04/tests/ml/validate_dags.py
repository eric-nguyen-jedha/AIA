#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de validation des DAGs Airflow — version stable pour CI/CD
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# =============================================================================
# 🛡️ MOCK COMPLET ET SIMPLE D'AIRFLOW (basé sur conftest.py)
# =============================================================================
# Liste exhaustive des modules Airflow utilisés dans les DAGs
modules_to_mock = [
    "airflow",
    "airflow.models",
    "airflow.models.Variable",
    "airflow.models.dag",
    "airflow.models.dagbag",
    "airflow.operators",
    "airflow.operators.python",
    "airflow.providers",
    "airflow.providers.amazon",
    "airflow.providers.amazon.aws",
    "airflow.providers.amazon.aws.hooks",
    "airflow.providers.amazon.aws.hooks.s3",
    "airflow.providers.postgres",
    "airflow.providers.postgres.hooks",
    "airflow.providers.postgres.hooks.postgres",
    "airflow.exceptions",
    "airflow.utils",
    "airflow.utils.dates",
]

for mod_name in modules_to_mock:
    sys.modules[mod_name] = MagicMock()

# Mock plugin custom
sys.modules["s3_to_postgres"] = MagicMock()

# Mock spécifique de Variable.get
class MockVariable:
    @staticmethod
    def get(key, default_var=None):
        fake_vars = {
            "BUCKET": "test-bucket",
            "AWS_ACCESS_KEY_ID": "fake_key",
            "AWS_SECRET_ACCESS_KEY": "fake_secret",
            "AWS_DEFAULT_REGION": "eu-west-3",
            "OPEN_WEATHER_API_KEY": "fake_api_key",
            "mlflow_uri": "http://localhost:8081",
        }
        return fake_vars.get(key, default_var or f"mock_{key}")

# Injecter dans le mock
sys.modules["airflow.models.Variable"].Variable = MockVariable
# =============================================================================

# Imports après le mocking
import importlib.util

def validate_dag_file(dag_path):
    print(f"📄 Validation de {dag_path.name}...")
    try:
        module_name = dag_path.stem
        spec = importlib.util.spec_from_file_location(module_name, str(dag_path))
        if spec is None:
            print("  ❌ Impossible de charger le module")
            return False

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Vérifier la présence d'au moins un DAG
        from airflow.models import DAG
        dags_found = [
            attr.dag_id for attr_name in dir(module)
            if isinstance(getattr(module, attr_name), DAG)
        ]

        if not dags_found:
            print("  ⚠️  Aucun DAG trouvé")
            return False

        print(f"  ✅ DAGs trouvés: {', '.join(dags_found)}")
        return True

    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False


def main():
    # Chemin pour BLOC_04/tests/ml/validate_dags.py
    dags_dir = Path(__file__).parent.parent.parent / "dags_ml"

    print("=" * 60)
    print("🔍 VALIDATION DES DAGS AIRFLOW")
    print("=" * 60)

    dags_to_validate = [
        "realtime_prediction_forecast.py",
        "paris_meteo_ml_pipeline.py"
    ]

    results = {}
    for filename in dags_to_validate:
        dag_path = dags_dir / filename
        if not dag_path.exists():
            print(f"❌ Fichier non trouvé: {filename}")
            results[filename] = False
            continue

        results[filename] = validate_dag_file(dag_path)
        print()

    print("=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    print(f"Total: {total}")
    print(f"✅ Réussis: {passed}")
    print(f"❌ Échoués: {failed}")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
