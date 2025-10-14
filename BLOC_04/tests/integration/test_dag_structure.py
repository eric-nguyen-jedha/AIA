# tests/integration/test_dag_integrity.py

import os
import sys
from unittest.mock import patch

# Optionnel : mock les modules problématiques si tu ne veux pas installer certains providers
# Mais ici, on suppose qu'au moins `apache-airflow` est installé

def test_dag_loads_correctly():
    """Test que le DAG se charge sans erreur d'import."""
    from airflow.models import DagBag

    # Charge uniquement le fichier du DAG cible
    dag_path = os.path.join(os.path.dirname(__file__), "..", "..", "dags", "meteo_paris.py")
    dag_path = os.path.abspath(dag_path)

    with patch.dict(os.environ, {"AIRFLOW__CORE__LOAD_DEFAULT_CONNECTIONS": "False"}):
        dag_bag = DagBag(dag_folder=dag_path, include_examples=False)

    # Vérifie qu'il n'y a pas d'erreur d'import
    assert len(dag_bag.import_errors) == 0, f"Import errors: {dag_bag.import_errors}"

    dag = dag_bag.get_dag("etl_weather_dag")
    assert dag is not None, "DAG etl_weather_dag not found"

    expected_tasks = {
        "fetch_weather_data",
        "transform_and_append_weather_data",
        "create_weather_table",
        "transfer_weather_data_to_postgres",
    }
    actual_tasks = set(dag.task_dict.keys())
    assert actual_tasks == expected_tasks, f"Expected tasks: {expected_tasks}, got: {actual_tasks}"


def test_dag_dependencies():
    """Test les dépendances entre les tâches."""
    from airflow.models import DagBag

    dag_path = os.path.join(os.path.dirname(__file__), "..", "..", "dags", "meteo_paris.py")
    dag_path = os.path.abspath(dag_path)

    with patch.dict(os.environ, {"AIRFLOW__CORE__LOAD_DEFAULT_CONNECTIONS": "False"}):
        dag_bag = DagBag(dag_folder=dag_path, include_examples=False)

    dag = dag_bag.get_dag("etl_weather_dag")
    assert dag is not None

    # Définition des dépendances attendues
    expected_deps = {
        "fetch_weather_data": ["transform_and_append_weather_data"],
        "transform_and_append_weather_data": ["create_weather_table"],
        "create_weather_table": ["transfer_weather_data_to_postgres"],
    }

    for upstream_task_id, expected_downstreams in expected_deps.items():
        upstream_task = dag.get_task(upstream_task_id)
        actual_downstreams = list(upstream_task.downstream_task_ids)
        assert set(actual_downstreams) == set(expected_downstreams), \
            f"Downstream tasks of '{upstream_task_id}' mismatch: expected {expected_downstreams}, got {actual_downstreams}"