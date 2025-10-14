# tests/unit/test_csv_to_neondb.py

import sys
from unittest.mock import patch, MagicMock
import pytest

# 🔑 NE PAS mock sys.modules["s3_to_postgres"] → cela casse tout !

# ✅ Import direct (nécessite que le fichier soit trouvable)
# Assure-toi que le dossier parent de `s3_to_postgres.py` est dans le PYTHONPATH
# Ou place ce fichier dans un package valide.

# Pour que pytest trouve s3_to_postgres.py, on l'ajoute temporairement au path
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "plugins"))

from s3_to_postgres import S3ToPostgresOperator


@patch("s3_to_postgres.S3Hook")
@patch("s3_to_postgres.PostgresHook")
@patch("s3_to_postgres.pd.read_csv")
def test_s3_to_postgres_operator(mock_read_csv, mock_postgres_hook_class, mock_s3_hook_class):
    """Test que l'opérateur S3ToPostgres télécharge le CSV et l'écrit en base."""
    
    # Mock S3Hook
    mock_s3_instance = MagicMock()
    mock_s3_hook_class.return_value = mock_s3_instance
    mock_s3_instance.download_file.return_value = "/tmp/weather_paris_fect.csv"

    # Mock PostgresHook
    mock_postgres_instance = MagicMock()
    mock_postgres_hook_class.return_value = mock_postgres_instance
    mock_engine = MagicMock()
    mock_postgres_instance.get_sqlalchemy_engine.return_value = mock_engine

    # Mock DataFrame
    mock_df = MagicMock()
    mock_read_csv.return_value = mock_df

    # Instancier l'opérateur
    operator = S3ToPostgresOperator(
        task_id="test_transfer",
        bucket="TEST_BUCKET",
        key="weather_paris_fect.csv",
        table="weather_data",
        postgres_conn_id="neon_db_conn",
        aws_conn_id="aws_default"
    )

    # Exécution
    operator.execute(context={})

    # Vérifications
    mock_s3_instance.download_file.assert_called_once_with(
        key="weather_paris_fect.csv",
        bucket_name="TEST_BUCKET",
        local_path="/tmp"
    )

    mock_read_csv.assert_called_once_with("/tmp/weather_paris_fect.csv", header=None)

    mock_df.to_sql.assert_called_once_with(
        "weather_data",
        mock_engine,
        if_exists="replace",
        index=False
    )
