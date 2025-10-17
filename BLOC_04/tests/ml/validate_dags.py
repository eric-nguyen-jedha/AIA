#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de validation des DAGs Airflow
Vérifie que les DAGs peuvent être importés sans erreur
"""

import sys
import os
from pathlib import Path
import importlib.util
from unittest.mock import MagicMock

# =============================================================================
# 🛡️ MOCK GLOBAL DES MODULES AIRFLOW (comme dans conftest.py)
# =============================================================================
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
    "airflow.providers.postgres",
    "airflow.providers.postgres.hooks",
    "airflow.providers.postgres.hooks.postgres",
]

for mod_name in _airflow_modules:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

# Mock aussi le plugin custom
sys.modules["s3_to_postgres"] = MagicMock()

# Mock spécifique de Variable.get pour retourner des valeurs factices
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
        if key in fake_vars:
            return fake_vars[key]
        if default_var is not None:
            return default_var
        raise KeyError(f"Variable {key} does not exist")

# Remplacer la classe Variable par notre mock
sys.modules["airflow.models.Variable"].Variable = MockVariable
# =============================================================================

def validate_dag_file(dag_path):
    """Valider un fichier DAG individuel"""
    print(f"📄 Validation de {dag_path.name}...")
    
    try:
        module_name = dag_path.stem
        spec = importlib.util.spec_from_file_location(module_name, str(dag_path))
        if spec is None:
            print(f"  ❌ Impossible de charger le module {dag_path}")
            return False

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Vérifier qu'il contient au moins un DAG
        from airflow.models import DAG
        dags_found = [
            attr.dag_id for attr_name in dir(module)
            if isinstance(getattr(module, attr_name), DAG)
        ]

        if not dags_found:
            print(f"  ⚠️  Aucun DAG trouvé dans {dag_path.name}")
            return False

        print(f"  ✅ DAGs trouvés: {', '.join(dags_found)}")
        return True

    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False


def main():
    # Chemin pour BLOC_04/tests/ml/validate_dags.py
    dags_dir = Path(__file__).parent.parent.parent / 'dags_ml'
    
    print("=" * 60)
    print("🔍 VALIDATION DES DAGS AIRFLOW")
    print("=" * 60)
    
    dags_to_validate = [
        'realtime_prediction_forecast.py',
        'paris_meteo_ml_pipeline.py'
    ]
    
    results = {}
    for dag_filename in dags_to_validate:
        dag_path = dags_dir / dag_filename
        
        if not dag_path.exists():
            print(f"❌ Fichier non trouvé: {dag_filename}")
            results[dag_filename] = False
            continue
        
        results[dag_filename] = validate_dag_file(dag_path)
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


if __name__ == '__main__':
    main()
