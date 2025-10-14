from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime
import os

def run_mlflow_experiment():
    import mlflow
    import pandas as pd
    from sklearn.datasets import load_iris
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split

    # === Charger les variables Airflow dans l'environnement ===
    os.environ["AWS_ACCESS_KEY_ID"] = Variable.get("AWS_ACCESS_KEY_ID")
    os.environ["AWS_SECRET_ACCESS_KEY"] = Variable.get("AWS_SECRET_ACCESS_KEY")
    os.environ["AWS_DEFAULT_REGION"] = Variable.get("AWS_DEFAULT_REGION")
    os.environ["ARTIFACT_STORE_URI"] = Variable.get("ARTIFACT_STORE_URI", default_var="")

    mlflow.set_tracking_uri("http://host.docker.internal:8081")

    # === Nom de l'expérience ===
    EXPERIMENT_NAME = "dag_mlflow_credentials"
    mlflow.set_experiment(EXPERIMENT_NAME)

    # === Charger dataset Iris ===
    iris = load_iris()
    X = pd.DataFrame(data=iris["data"], columns=iris["feature_names"])
    y = pd.Series(data=iris["target"], name="target")
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

    # === Activer autologging ===
    mlflow.sklearn.autolog(log_models=True, log_input_examples=True, log_model_signatures=True)

    # === Démarrer un run ===
    with mlflow.start_run(run_name="run1"):
        lr = LogisticRegression(max_iter=200)
        lr.fit(X_train, y_train)
        accuracy = lr.score(X_test, y_test)

        # Log manuel de la métrique (optionnel)
        mlflow.log_metric("test_accuracy", accuracy)

        print(f"LogisticRegression model")
        print(f"Accuracy: {accuracy}")

# === Définition du DAG ===
with DAG(
    dag_id="mlflow_iris_experiment",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["mlflow", "iris", "example"],
) as dag:

    run_experiment = PythonOperator(
        task_id="run_mlflow_experiment",
        python_callable=run_mlflow_experiment,
    )
