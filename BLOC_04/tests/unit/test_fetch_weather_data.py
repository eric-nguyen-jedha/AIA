#✅ Test 2 — _fetch_weather_data

import json
from unittest.mock import patch, MagicMock
from dags.etl_weather_dag import _fetch_weather_data

@patch("dags.etl_weather_dag.requests.get")
@patch("dags.etl_weather_dag.Variable.get")
def test_fetch_weather_data(mock_var, mock_get, mock_ti):
    mock_var.return_value = "FAKE_API_KEY"

    fake_resp = MagicMock(status_code=200)
    fake_resp.json.return_value = {
        "weather": [{"main": "Clouds", "description": "few clouds"}],
        "main": {"temp": 10, "feels_like": 9, "pressure": 1013, "humidity": 75},
        "dt": 1700000000,
        "clouds": {"all": 20},
        "wind": {"speed": 3.0, "deg": 200},
    }
    mock_get.return_value = fake_resp

    _fetch_weather_data(ti=mock_ti)

    mock_ti.xcom_push.assert_called_once()
    args, kwargs = mock_ti.xcom_push.call_args
    assert kwargs["key"] == "local_json_path"
    assert "weather" in open(kwargs["value"]).read()  # vérifie contenu JSON
