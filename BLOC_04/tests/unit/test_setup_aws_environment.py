import os
from unittest.mock import patch
from dags.etl_weather_dag import setup_aws_environment

@patch("dags.etl_weather_dag.Variable.get")
def test_setup_aws_environment(mock_get):
    mock_get.side_effect = ["FAKE_KEY", "FAKE_SECRET", "eu-west-3"]
    setup_aws_environment()

    assert os.environ["AWS_ACCESS_KEY_ID"] == "FAKE_KEY"
    assert os.environ["AWS_SECRET_ACCESS_KEY"] == "FAKE_SECRET"
    assert os.environ["AWS_DEFAULT_REGION"] == "eu-west-3"
