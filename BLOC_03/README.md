# Pipeline de Détection de Fraude avec Airflow, XGBoost et MLflow

Ce projet implémente un **pipeline automatisé de détection de fraude** en deux étapes :
1. **Vérification de la qualité des données** (Drift, tests statistiques) avec Evidently.
2. **Entraînement d'un modèle XGBoost** et suivi des expériences avec MLflow.

Le pipeline est orchestré avec **Apache Airflow**, et les artefacts sont stockés sur S3.

---

## 📌 Architecture Globale

```mermaid
graph TD
    subgraph "Data Source & Ingestion"
        A[S3 CSV] -->|Pull| B[Data Pull & Check]
        C[API Transactions] -->|Real-time| D[Predict]
    end

    subgraph "Airflow DAGs (Orchestration)"
        B[Data Pull & Check] --> E[ML Training]
        E --> F[Model Registry]
        D --> G[Email not.]
    end

    subgraph "MLflow (Model Management)"
        F[Model Registry] --> H[Metrics]
        F --> I[Artifact Model]
        H --> J[PostgreSQL NEON]
        I --> K[S3 Model]
    end

    subgraph "Output & Monitoring"
        G --> L[Anti Fraud Team Email]
        D --> M[S3 Predict Backup]
        M --> N[PostgreSQL NEON]
        N --> O[Streamlit Dashboard]
        O --> P[Dashboard for Anti Fraud Team Stakeholder]
    end

    %% Connexions externes
    style A fill:#FFD700,stroke:#333
    style C fill:#4CAF50,stroke:#333
    style B fill:#2196F3,stroke:#fff
    style D fill:#2196F3,stroke:#fff
    style E fill:#9C27B0,stroke:#fff
    style F fill:#FF9800,stroke:#fff
    style H fill:#8BC34A,stroke:#fff
    style I fill:#FF5722,stroke:#fff
    style J fill:#E91E63,stroke:#fff
    style K fill:#00BCD4,stroke:#fff
    style L fill:#FFEB3B,stroke:#333
    style M fill:#009688,stroke:#fff
    style N fill:#673AB7,stroke:#fff
    style O fill:#FF9800,stroke:#fff
    style P fill:#3F51B5,stroke:#fff

    %% Flèches
    A --> B
    C --> D
    B --> E
    E --> F
    F --> H
    F --> I
    H --> J
    I --> K
    D --> G
    G --> L
    D --> M
    M --> N
    N --> O
    O --> P

    %% Labels
    A:::data-source
    C:::api-source
    B:::airflow-task
    D:::airflow-task
    E:::airflow-task
    F:::mlflow-component
    H:::mlflow-component
    I:::mlflow-component
    J:::storage
    K:::storage
    L:::notification
    M:::backup
    N:::storage
    O:::dashboard
    P:::stakeholder

    classDef data-source fill:#FFD700,stroke:#333,stroke-width:2px
    classDef api-source fill:#4CAF50,stroke:#333,stroke-width:2px
    classDef airflow-task fill:#2196F3,stroke:#fff,stroke-width:2px
    classDef mlflow-component fill:#FF9800,stroke:#fff,stroke-width:2px
    classDef storage fill:#673AB7,stroke:#fff,stroke-width:2px
    classDef notification fill:#FFEB3B,stroke:#333,stroke-width:2px
    classDef backup fill:#009688,stroke:#fff,stroke-width:2px
    classDef dashboard fill:#FF9800,stroke:#fff,stroke-width:2px
    classDef stakeholder fill:#3F51B5,stroke:#fff,stroke-width:2px

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

## 1️⃣ DAG evidently_data_quality_fraud

Objectif : Vérifier la qualité des données avant l'entraînement.
Fonctionnalités :

- download_fraud_csv : Télécharge le dataset fraudTest.csv depuis une URL.
- evidently_check : Génère un rapport de drift (visuel) et une test suite (textuelle) avec Evidently.
- upload_reports_to_s3 : Sauvegarde les rapports en local et sur S3.
- send_evidently_report_email : Envoie un email de résumé avec les liens vers les rapports.
- trigger_xgboost_dag : Déclenche le DAG suivant (fraud_detection_xgboost_dag) en passant le chemin du fichier CSV.

## 2️⃣ DAG fraud_detection_xgboost_dag
Objectif : Entraîner un modèle XGBoost pour détecter les fraudes.
Fonctionnalités :

- get_data : Récupère le chemin du fichier CSV passé par le DAG précédent (dag_run.conf).
- clean_data : Nettoie les données (feature engineering, encodage, etc.).
- train_model : Entraîne un modèle XGBoost avec suivi des métriques via MLflow. Sauvegarde la matrice de confusion et log le modèle.

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