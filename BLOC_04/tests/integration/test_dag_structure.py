# tests/integration/test_dag_structure.py

import os
import sys
from unittest.mock import patch, MagicMock

# 🔑 Mock du plugin custom pour éviter ImportError
sys.modules["s3_to_postgres"] = MagicMock()

def test_dag_loads_correctly():
    from airflow.models import DagBag

    dag_path = os.path.join(os.path.dirname(__file__), "..", "..", "dags", "meteo_paris.py")
    dag_path = os.path.abspath(dag_path)

    with patch.dict(os.environ, {"AIRFLOW__CORE__LOAD_DEFAULT_CONNECTIONS": "False"}):
        dag_bag = DagBag(dag_folder=dag_path, include_examples=False)

    # Débogage (optionnel) — à retirer en prod
    # print("Import errors:", dag_bag.import_errors)

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
    from airflow.models import DagBag

    dag_path = os.path.join(os.path.dirname(__file__), "..", "..", "dags", "meteo_paris.py")
    dag_path = os.path.abspath(dag_path)

    with patch.dict(os.environ, {"AIRFLOW__CORE__LOAD_DEFAULT_CONNECTIONS": "False"}):
        dag_bag = DagBag(dag_folder=dag_path, include_examples=False)

    dag = dag_bag.get_dag("etl_weather_dag")
    assert dag is not None

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
