# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os
import json
import requests

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

import mlflow
import boto3

# ----------------------------
# Configuration DAG
# ----------------------------
default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
}

dag = DAG(
    'real_time_weather_prediction',
    default_args=default_args,
    description='Prédiction météo en temps réel avec MLflow et OpenWeather API',
    schedule=timedelta(minutes=5),
    catchup=False,
    tags=['ml', 'weather', 'prediction', 'real-time', 'openweather', 'mlflow'],
)

# ----------------------------
# Variables Airflow / config
# ----------------------------
CITIES = {
    'paris': {'lat': 48.8566, 'lon': 2.3522, 'name': 'Paris'},
    'toulouse': {'lat': 43.6047, 'lon': 1.4442, 'name': 'Toulouse'},
    'lyon': {'lat': 45.7640, 'lon': 4.8357, 'name': 'Lyon'},
    'marseille': {'lat': 43.2965, 'lon': 5.3698, 'name': 'Marseille'},
    'nantes': {'lat': 47.2184, 'lon': -1.5536, 'name': 'Nantes'}
}

BUCKET = Variable.get("BUCKET")

# Mapping des codes vers les labels météo
# Basé sur l'ordre alphabétique : Clear, Clouds, Fog, Rain, Snow
WEATHER_CODE_MAPPING = {
    0: 'Clear',
    1: 'Clouds',
    2: 'Fog',
    3: 'Rain',
    4: 'Snow'
}
