#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de validation des DAGs Airflow — version robuste pour CI/CD
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# =============================================================================
# 🛡️ MOCK COMPLET D'AIRFLOW (doit être en TOUT PREMIER)
# =============================================================================
# Simule tout le package airflow comme un module vide mais importable
class MockAirflowModule:
    def __init__(self, name):
        self.__name__ = name
        self.__path__ = []
        self.__file__ = f"<mocked {name}>"

    def __getattr__(self, name):
        # Crée des sous-modules à la volée (ex: airflow.operators, airflow.models, etc.)
        fullname = f"{self.__name__}.{name}"
        mod = MockAirflowModule(fullname)
        sys.modules[fullname] = mod
        return mod

# Remplace le module 'airflow' par un mock dynamique
sys.modules["airflow"] = MockAirflowModule("airflow")

# Mock aussi les modules courants utilisés dans les DAGs
sys.modules["airflow.models"] = MagicMock()
sys.modules["airflow.models.Variable"] = MagicMock()
sys.modules["airflow.operators"] = MagicMock()
sys.modules["airflow.operators.python"] = MagicMock()
sys.modules["airflow.providers"] = MagicMock()
sys.modules["airflow.providers.amazon"] = MagicMock()
sys.modules["airflow.providers.amazon.aws"] = MagicMock()
sys.modules["airflow.providers.amazon.aws.hooks"] = MagicMock()
sys.modules["airflow.providers.amazon.aws.hooks.s3"] = MagicMock()
sys.modules["airflow.providers.postgres"] = MagicMock()
sys.modules["airflow.providers.postgres.hooks"] = MagicMock()
sys.modules["airflow.providers.postgres.hooks.postgres"] = MagicMock()

# Mock plugin custom
sys.modules["s3_to_postgres"] = MagicMock()

# Mock Variable.get pour éviter les erreurs de "table variable"
class MockVariable:
    @staticmethod
    def get(key, default_var=None):
        return {
            "BUCKET": "test-bucket",
            "AWS_ACCESS_KEY_ID": "fake",
            "AWS_SECRET_ACCESS_KEY": "fake",
            "AWS_DEFAULT_REGION": "eu-west-3",
            "OPEN_WEATHER_API_KEY": "fake_key",
            "mlflow_uri": "http://localhost:8081",
        }.get(key, default_var or f"mock_value_for_{key}")

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
            print(f"  ❌ Impossible de charger le module")
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
            print(f"  ⚠️  Aucun DAG trouvé")
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
