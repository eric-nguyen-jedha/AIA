# Pipeline de Détection de Fraude avec Airflow, XGBoost et MLflow

Ce projet implémente un **pipeline automatisé de détection de fraude** en deux étapes :
1. **Vérification de la qualité des données** (Drift, tests statistiques) avec Evidently.
2. **Entraînement d'un modèle XGBoost** et suivi des expériences avec MLflow.

Le pipeline est orchestré avec **Apache Airflow**, et les artefacts sont stockés sur S3.

---

## 📌 Architecture Globale

```mermaid
graph TD
    %% === Sources de données ===
    A[S3 CSV] --> B[Data Pull & Check]
    C[API Transactions] --> D[Predict]

    %% === Nouvelle notification : Data Team ===
    B --> E[Email Alert to Data Team]

    %% === Orchestration Airflow ===
    B --> F[ML Training]
    F --> G[Model Registry]
    D --> H[Email Notification to Anti Fraud Team]

    %% === MLflow ===
    G --> I[Metrics]
    G --> J[Artifact Model]
    I --> K[PostgreSQL NEON]
    J --> L[S3 Model]

    %% === Sauvegarde & Monitoring ===
    D --> M[S3 Predict Backup]
    M --> N[PostgreSQL NEON]
    N --> O[Streamlit Dashboard]
    O --> P[Dashboard for Anti Fraud Team Stakeholder]

    %% === Styles sobres en gris ===
    classDef source fill:#f8f9fa,stroke:#666;
    classDef process fill:#f1f3f5,stroke:#666;
    classDef storage fill:#e9ecef,stroke:#666;
    classDef notification fill:#ffffff,stroke:#666,stroke-dasharray: 3 3;

    class A,C source
    class B,D,F,G,H,E,M,O process
    class K,L,N storage
    class H,E,P notification

```


## 📂 Structure du Projet

```
.
├── dags/
│   ├── fraud_detection_datacheck.py         # DAG 1 : Vérification qualité des données
│   ├── fraud_detection_ml.py                # DAG 2 : Entrainement du modèle Xgboost et enregistrement dans MLFLOW
│   ├── raud_detection_predict.py            # DAG 3 : Prediction temps réel d'un Fraude
│   └── fraud_detection_recap24h.py          # DAG 2 : Reporting 24h passées et envoie de notification par mail
├── data/                                    # Dossier local pour les données (monté dans Airflow)
│   ├── fraudTest.csv                        # Dataset des transactions src : Kaggle
│   ├── current_transactions_raw*.csv        # fichier brut src: API
│   ├── current_transactions_clean*.csv      # Fichier nettoyé prêt pour une prediction
│   └── fraud_detection_on_going.csv         # Fichier historique des prédictions
├── reports/                                 # Rapports Evidently (Drift, Test Suite)
└── README.md

```

## 1️⃣ DAG fraud_detection_01_evidently_data_quality

Objectif : Vérifier la qualité des données avant l'entraînement.
Fonctionnalités :

- download_fraud_csv : Télécharge le dataset fraudTest.csv depuis une URL.
- evidently_check : Génère un rapport de drift (visuel) et une test suite (textuelle) avec Evidently.
- upload_reports_to_s3 : Sauvegarde les rapports en local et sur S3.
- send_evidently_report_email : Envoie un email de résumé avec les liens vers les rapports.
- trigger_xgboost_dag : Déclenche le DAG suivant (fraud_detection_xgboost_dag) en passant le chemin du fichier CSV.

## 2️⃣ DAG fraud_detection_02_xgboost_dag
Objectif : Entraîner un modèle XGBoost pour détecter les fraudes.
Fonctionnalités :

- load_csv : Récupère le chemin du fichier CSV passé par le DAG précédent (dag_run.conf).
- clean_data : Nettoie les données (feature engineering, encodage, etc.).
- train_mlflow : Entraîne un modèle XGBoost avec suivi des métriques via MLflow. Sauvegarde la matrice de confusion et log le modèle.

## 2️⃣ DAG fraud_detection_03_prediction_api
Objectif : Faire une prédiction en temps réel d'une Fraude .
Fonctionnalités :

- fetch_transactions : Récupère la transaction qui vient de l'API.
- preprocess_data : Nettoie les données et les rend conforme au modèle d'entrainement
- predict_and_save : Faire une prédiction avec le code Predict de MLFLOW et sauvegarder le résultat dans un CSV mais aussi dans la Base Neon BD (PostgreSQL)
- upload_and_alert : Upload les résultats dans un fichier CSV et envoie une notification à l'équipe DATA

## Variable #Airflow

Variable,Description
- AWS_ACCESS_KEY_ID,Clé AWS pour accéder à S3.
- AWS_SECRET_ACCESS_KEY,Secret AWS.
- BUCKET,Nom du bucket S3 pour les rapports.
- ARTIFACT_STORE_URI,URI du stockage MLflow.
- BACKEND_STORE_URI_FP,URI du backend MLflow.

## 🔧 Comment Lancer le Pipeline ?
1. Déployer les DAGs

Copier les fichiers .py dans le dossier dags/ d'Airflow.
Activer les DAGs dans l'UI Airflow.

2. Exécuter manuellement (optionnel)

Dans l'UI Airflow, cliquer sur Trigger DAG pour evidently_data_quality_fraud.
Le DAG XGBoost sera déclenché automatiquement.

3. Vérifier les résultats

Rapports : Voir les emails envoyés ou les fichiers dans le bucket S3.
Modèle : Consulter l'expérience MLflow à l'URL configurée.


⚠️ Points d'Attention

- Dépendances : Vérifier que toutes les librairies sont installées dans l'environnement Airflow.
- Permissions S3 : Le rôle IAM doit avoir les droits s3:PutObject et s3:GetObject.
- MLflow : L'URI du tracking doit être accessible depuis Airflow. MLFLOW est installé sur Hugging Face dans un Docker 
- Chemin des fichiers : Le dossier /opt/airflow/data doit être monté et accessible en écriture.