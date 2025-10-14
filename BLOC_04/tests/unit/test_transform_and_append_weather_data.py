#✅ Test 3 — _transform_and_append_weather_data
import json
import pandas as pd
from unittest.mock import patch, MagicMock
from dags.etl_weather_dag import _transform_and_append_weather_data

@patch("dags.etl_weather_dag.setup_aws_environment")
@patch("dags.etl_weather_dag.os.path.exists", return_value=True)
@patch("dags.etl_weather_dag.S3Hook")
@patch("builtins.open", new_callable=MagicMock)
@patch("dags.etl_weather_dag.Variable.get")
def test_transform_and_append_weather_data(mock_var, mock_open, mock_s3, mock_exists, mock_setup, mock_ti):
    mock_var.side_effect = ["FAKE_BUCKET"]
    mock_ti.xcom_pull.return_value = "/tmp/test_weather.json"

    fake_json = {
        "dt": 1700000000,
        "main": {"temp": 20, "feels_like": 19, "pressure": 1000, "humidity": 50},
        "clouds": {"all": 10},
        "wind": {"speed": 3.5, "deg": 180},
        "weather": [{"main": "Clear", "description": "sunny"}],
    }

    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(fake_json)

    _transform_and_append_weather_data(ti=mock_ti)

    mock_ti.xcom_push.assert_any_call(key="weather_csv_key", value="weather_paris_fect.csv")
    mock_s3.assert_called()
