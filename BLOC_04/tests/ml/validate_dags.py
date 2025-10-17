#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de validation des DAGs Airflow
Vérifie que les DAGs peuvent être importés sans erreur
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire des DAGs au path
dags_dir = Path(__file__).parent.parent / 'dags_ml'
sys.path.insert(0, str(dags_dir))

def validate_dag_file(dag_file):
    """Valider un fichier DAG individuel"""
    print(f"📄 Validation de {dag_file.name}...")
    
    try:
        # Essayer d'importer le module
        module_name = dag_file.stem
        spec = __import__(module_name)
        
        # Vérifier qu'il contient au moins un DAG
        from airflow.models import DAG
        dags_found = []
        
        for attr_name in dir(spec):
            attr = getattr(spec, attr_name)
            if isinstance(attr, DAG):
                dags_found.append(attr.dag_id)
        
        if not dags_found:
            print(f"  ⚠️  Aucun DAG trouvé dans {dag_file.name}")
            return False
        
        print(f"  ✅ DAGs trouvés: {', '.join(dags_found)}")
        return True
        
    except SyntaxError as e:
        print(f"  ❌ Erreur de syntaxe: {e}")
        return False
    except ImportError as e:
        print(f"  ❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False


def main():
    """Valider tous les fichiers DAG"""
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
    
    if failed > 0:
        print("\n❌ La validation a échoué!")
        sys.exit(1)
    else:
        print("\n✅ Tous les DAGs sont valides!")
        sys.exit(0)


if __name__ == '__main__':
    main()
