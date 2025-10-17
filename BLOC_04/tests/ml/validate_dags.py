#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de validation des DAGs Airflow — version stable pour CI/CD
Vérifie que les DAGs ML peuvent être importés sans erreur
"""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# =============================================================================
# 🛡️ DÉSACTIVER LA BASE DE DONNÉES AIRFLOW
# =============================================================================
# Forcer Airflow à ne pas utiliser de base de données
os.environ['AIRFLOW__CORE__UNIT_TEST_MODE'] = 'True'
os.environ['AIRFLOW__DATABASE__SQL_ALCHEMY_CONN'] = 'sqlite:///:memory:'

# =============================================================================
# 🛡️ MOCK COMPLET D'AIRFLOW - DOIT ÊTRE FAIT AVANT TOUT IMPORT
# =============================================================================

# Créer un vrai module mock pour airflow.models
class AirflowModelsMock:
    """Module mock pour airflow.models avec Variable intégré"""
    pass

# Liste des modules Airflow à mocker
modules_to_mock = [
    "airflow",
    "airflow.models.dag",
    "airflow.models.baseoperator",
    "airflow.operators",
    "airflow.operators.python",
    "airflow.providers",
    "airflow.providers.standard",
    "airflow.providers.standard.operators",
    "airflow.providers.standard.operators.python",
    "airflow.providers.amazon",
    "airflow.providers.amazon.aws",
    "airflow.providers.amazon.aws.hooks",
    "airflow.providers.amazon.aws.hooks.s3",
    "airflow.exceptions",
    "airflow.utils",
    "airflow.utils.dates",
]

for mod_name in modules_to_mock:
    sys.modules[mod_name] = MagicMock()

# Mock des dépendances externes
sys.modules["mlflow"] = MagicMock()
sys.modules["mlflow.pyfunc"] = MagicMock()
sys.modules["mlflow.xgboost"] = MagicMock()
sys.modules["mlflow.tracking"] = MagicMock()
sys.modules["boto3"] = MagicMock()
sys.modules["requests"] = MagicMock()

# Mock spécifique de Variable.get AVANT d'importer airflow.models
class MockVariable:
    @staticmethod
    def get(key, default_var=None):
        """Retourne toujours des chaînes valides"""
        fake_vars = {
            "BUCKET": "test-bucket",
            "AWS_ACCESS_KEY_ID": "fake_key",
            "AWS_SECRET_ACCESS_KEY": "fake_secret",
            "AWS_DEFAULT_REGION": "eu-west-3",
            "OPEN_WEATHER_API_KEY": "fake_api_key",
            "mlflow_uri": "http://localhost:8081",
            "ARTIFACT_STORE_URI": "s3://test-bucket/mlflow"
        }
        result = fake_vars.get(key)
        if result is not None:
            return str(result)
        if default_var is not None:
            return str(default_var)
        return f"mock_{key}"

# Créer un module airflow.models personnalisé
airflow_models_mock = type(sys)('airflow.models')
airflow_models_mock.Variable = MockVariable
sys.modules["airflow.models"] = airflow_models_mock
sys.modules["airflow.models.Variable"] = type(sys)('airflow.models.Variable')
sys.modules["airflow.models.Variable"].Variable = MockVariable

# Mock de DAG avec un attribut dag_id pour la détection
class MockDAG:
    def __init__(self, dag_id, *args, **kwargs):
        self.dag_id = str(dag_id)  # Force string
        self.default_args = kwargs.get('default_args', {})
        self.description = str(kwargs.get('description', ''))
        
        # Gérer schedule qui peut être string ou timedelta
        schedule = kwargs.get('schedule', kwargs.get('schedule_interval'))
        if schedule is not None:
            self.schedule = str(schedule) if not isinstance(schedule, str) else schedule
        else:
            self.schedule = None
            
        self.catchup = bool(kwargs.get('catchup', False))
        
        # Gérer tags qui doit être une liste
        tags = kwargs.get('tags', [])
        if isinstance(tags, (list, tuple)):
            self.tags = [str(t) for t in tags]
        else:
            self.tags = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def __str__(self):
        return f"DAG({self.dag_id})"
    
    def __repr__(self):
        return f"MockDAG(dag_id='{self.dag_id}')"

sys.modules["airflow"].DAG = MockDAG
sys.modules["airflow.models"].DAG = MockDAG
sys.modules["airflow.models.dag"].DAG = MockDAG

# Mock de PythonOperator avec support de l'opérateur >>
class MockPythonOperator:
    def __init__(self, *args, **kwargs):
        self.task_id = str(kwargs.get('task_id', 'mock_task'))
        self.python_callable = kwargs.get('python_callable')
        self.dag = kwargs.get('dag')
        self.kwargs = kwargs  # Stocker tous les kwargs
    
    def __rshift__(self, other):
        """Support de l'opérateur >> pour les dépendances"""
        return other
    
    def __lshift__(self, other):
        """Support de l'opérateur << pour les dépendances"""
        return self
    
    def set_upstream(self, other):
        """Méthode alternative pour définir les dépendances"""
        pass
    
    def set_downstream(self, other):
        """Méthode alternative pour définir les dépendances"""
        pass
    
    def __str__(self):
        return f"PythonOperator({self.task_id})"
    
    def __repr__(self):
        return f"MockPythonOperator(task_id='{self.task_id}')"

# Appliquer le mock à tous les imports possibles de PythonOperator
sys.modules["airflow.operators.python"].PythonOperator = MockPythonOperator
if "airflow.providers.standard" in sys.modules:
    if "airflow.providers.standard.operators" not in sys.modules:
        sys.modules["airflow.providers.standard.operators"] = MagicMock()
    if "airflow.providers.standard.operators.python" not in sys.modules:
        sys.modules["airflow.providers.standard.operators.python"] = MagicMock()
    sys.modules["airflow.providers.standard.operators.python"].PythonOperator = MockPythonOperator

# Mock d'autres opérateurs si nécessaires
class MockBaseOperator:
    def __init__(self, *args, **kwargs):
        self.task_id = kwargs.get('task_id', 'mock_task')
        self.dag = kwargs.get('dag')
    
    def __rshift__(self, other):
        return other
    
    def __lshift__(self, other):
        return self

if "airflow.models.baseoperator" in sys.modules:
    sys.modules["airflow.models.baseoperator"].BaseOperator = MockBaseOperator

# =============================================================================
# Fonction de validation
# =============================================================================

import importlib.util

def validate_dag_file(dag_path):
    """Valider un fichier DAG individuel"""
    print(f"📄 Validation de {dag_path.name}...")
    
    try:
        # Charger le module
        module_name = dag_path.stem
        spec = importlib.util.spec_from_file_location(module_name, str(dag_path))
        
        if spec is None:
            print("  ❌ Impossible de créer la spec du module")
            return False
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        
        # Exécuter le module
        spec.loader.exec_module(module)
        
        # Chercher les DAGs dans le module
        dags_found = []
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            # Vérifier si c'est un MockDAG ou un objet avec dag_id
            if isinstance(attr, MockDAG) or (hasattr(attr, 'dag_id') and hasattr(attr, 'default_args')):
                dags_found.append(attr.dag_id)
        
        if not dags_found:
            print("  ⚠️  Aucun DAG trouvé dans le module")
            return False
        
        print(f"  ✅ DAGs trouvés: {', '.join(dags_found)}")
        return True
        
    except SyntaxError as e:
        print(f"  ❌ Erreur de syntaxe: {e}")
        print(f"     Ligne {e.lineno}: {e.text}")
        return False
    except ImportError as e:
        print(f"  ❌ Erreur d'import: {e}")
        import traceback
        print("     Détails:")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"  ❌ Erreur lors de la validation: {e}")
        print("     Détails de l'erreur:")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Valider tous les DAGs ML"""
    
    # Déterminer le chemin des DAGs
    # Si exécuté depuis BLOC_04/tests/ml/validate_dags.py
    script_dir = Path(__file__).parent
    
    # Essayer plusieurs chemins possibles
    possible_paths = [
        script_dir.parent.parent / "dags_ml",  # BLOC_04/dags_ml
        script_dir.parent.parent / "dags",      # BLOC_04/dags (si même répertoire)
        Path.cwd() / "dags_ml",                 # Si exécuté depuis BLOC_04
    ]
    
    dags_dir = None
    for path in possible_paths:
        if path.exists():
            dags_dir = path
            break
    
    if dags_dir is None:
        print("❌ Impossible de trouver le répertoire dags_ml/")
        print(f"   Chemins testés: {[str(p) for p in possible_paths]}")
        sys.exit(1)
    
    print("=" * 60)
    print("🔍 VALIDATION DES DAGS AIRFLOW ML")
    print("=" * 60)
    print(f"📂 Répertoire: {dags_dir}")
    print()
    
    # Liste des DAGs à valider
    dags_to_validate = [
        "realtime_prediction_forecast.py",
        "paris_meteo_ml_pipeline.py"
    ]
    
    results = {}
    for filename in dags_to_validate:
        dag_path = dags_dir / filename
        
        if not dag_path.exists():
            print(f"❌ Fichier non trouvé: {filename}")
            print(f"   Chemin complet: {dag_path}")
            results[filename] = False
            continue
        
        results[filename] = validate_dag_file(dag_path)
        print()
    
    # Résumé
    print("=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print(f"Total: {total}")
    print(f"✅ Réussis: {passed}")
    print(f"❌ Échoués: {failed}")
    print()
    
    if failed > 0:
        print("❌ La validation a échoué!")
        sys.exit(1)
    else:
        print("✅ Tous les DAGs sont valides!")
        sys.exit(0)


if __name__ == "__main__":
    main()
