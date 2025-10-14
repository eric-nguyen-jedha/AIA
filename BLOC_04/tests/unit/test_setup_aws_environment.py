import os
from unittest.mock import patch
import pytest
from dags.meteo_paris import setup_aws_environment


@patch("dags.meteo_paris.Variable.get")
def test_setup_aws_environment(mock_get):
    """Test de la configuration des variables AWS"""
    
    # Mock des Variables Airflow (appelées 3 fois dans l'ordre)
    mock_get.side_effect = ["FAKE_KEY", "FAKE_SECRET", "eu-west-3"]
    
    # Nettoyer les variables d'environnement avant le test
    for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"]:
        os.environ.pop(key, None)
    
    # Exécution
    setup_aws_environment()
    
    # Vérifications
    assert os.environ["AWS_ACCESS_KEY_ID"] == "FAKE_KEY"
    assert os.environ["AWS_SECRET_ACCESS_KEY"] == "FAKE_SECRET"
    assert os.environ["AWS_DEFAULT_REGION"] == "eu-west-3"
    
    # Vérifier que Variable.get a été appelé 3 fois avec les bons arguments
    assert mock_get.call_count == 3
    mock_get.assert_any_call("AWS_ACCESS_KEY_ID")
    mock_get.assert_any_call("AWS_SECRET_ACCESS_KEY")
    mock_get.assert_any_call("AWS_DEFAULT_REGION")


@patch("dags.meteo_paris.Variable.get")
def test_setup_aws_environment_missing_variable(mock_get):
    """Test de gestion d'erreur si une variable est manquante"""
    
    # Simuler une erreur KeyError (variable manquante)
    from airflow.exceptions import AirflowException
    mock_get.side_effect = AirflowException("Variable AWS_ACCESS_KEY_ID not found")
    
    # Nettoyer les variables d'environnement
    for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"]:
        os.environ.pop(key, None)
    
    # Doit lever une exception
    with pytest.raises(Exception):
        setup_aws_environment()


@patch("dags.meteo_paris.Variable.get")
def test_setup_aws_environment_cleanup(mock_get):
    """Test avec nettoyage après exécution"""
    
    mock_get.side_effect = ["TEST_KEY", "TEST_SECRET", "us-east-1"]
    
    # Setup
    setup_aws_environment()
    
    assert os.environ["AWS_ACCESS_KEY_ID"] == "TEST_KEY"
    
    # Cleanup pour ne pas polluer les autres tests
    for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"]:
        os.environ.pop(key, None)
