from airflow.models import DagBag

def test_dag_loads_correctly():
    dag_bag = DagBag(dag_folder="dags/", include_examples=False)
    assert len(dag_bag.import_errors) == 0, f"Import errors: {dag_bag.import_errors}"

    dag = dag_bag.get_dag(dag_id="etl_weather_dag")
    assert dag is not None
    assert set(dag.task_dict.keys()) == {
        "fetch_weather_data",
        "transform_and_append_weather_data",
        "create_weather_table",
        "transfer_weather_data_to_postgres",
    }

def test_dag_dependencies():
    dag_bag = DagBag(dag_folder="dags/", include_examples=False)
    dag = dag_bag.get_dag("etl_weather_dag")

    deps = {
        "fetch_weather_data": ["transform_and_append_weather_data"],
        "transform_and_append_weather_data": ["create_weather_table"],
        "create_weather_table": ["transfer_weather_data_to_postgres"],
    }

    for upstream, downstreams in deps.items():
        for d in downstreams:
            assert d in dag.task_dict[upstream].downstream_task_ids
