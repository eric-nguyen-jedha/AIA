# dags/weather_utils.py

import json
import logging
import os
from datetime import datetime
import requests
from airflow.models import Variable
from airflow.exceptions import AirflowException  # pour la gestion d'erreur

# Coordonnées de Paris
LAT = 48.8566
LON = 2.3522


def setup_aws_environment():
    """Configure les credentials AWS via Variables Airflow"""
    try:
        os.environ["AWS_ACCESS_KEY_ID"] = Variable.get("AWS_ACCESS_KEY_ID")
        os.environ["AWS_SECRET_ACCESS_KEY"] = Variable.get("AWS_SECRET_ACCESS_KEY")
        os.environ["AWS_DEFAULT_REGION"] = Variable.get("AWS_DEFAULT_REGION")
        logging.info("✓ AWS environment configured from Airflow Variables")
    except Exception as e:
        logging.error(f"❌ AWS setup failed: {str(e)}")
        raise


def fetch_weather_data(**context):
    """Appelle l'API OpenWeatherMap et sauvegarde le JSON local"""
    logging.info("Fetching weather data from OpenWeatherMap")
    api_key = Variable.get("OPEN_WEATHER_API_KEY")

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={api_key}&units=metric"
    resp = requests.get(url)
    if resp.status_code != 200:
        raise ValueError(f"Erreur API : {resp.status_code} - {resp.text}")

    filename = f"{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}_weather.json"
    local_path = f"/tmp/{filename}"
   
    with open(local_path, "w") as f:
        json.dump(resp.json(), f)
    
    context["ti"].xcom_push(key="local_json_path", value=local_path)
    logging.info(f"JSON saved locally: {local_path}")
