from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import os, sys

# Добавляем в sys.path путь к data_ingestion и utils (если ваши скрипты там лежат)
PROJECT_HOME = os.getenv("PROJECT_HOME", "/opt/airflow")
sys.path.insert(0, os.path.join(PROJECT_HOME, "data_ingestion"))
sys.path.insert(0, os.path.join(PROJECT_HOME, "utils"))

# Импортируем наши функции
from upload_to_s3 import upload_products_from_parquet
from postgres_to_s3 import export_customers
from s3_stage_loader import main as stage_loader_main

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="daily_shop_etl",
    default_args=default_args,
    description="Ежедневная загрузка товаров, клиентов и копирование Parquet",
    start_date=datetime(2025, 6, 2, 2, 0),
    schedule_interval="0 2 * * *",
    catchup=False,
    tags=["shop", "etl", "daily"],
) as dag:

    task_upload_products = PythonOperator(
        task_id="upload_products_to_raw",
        python_callable=upload_products_from_parquet,
        op_kwargs={
            "local_parquet_path": "/opt/airflow/data_ingestion/products.parquet"
        },
    )

    task_export_customers = PythonOperator(
        task_id="export_customers_to_raw",
        python_callable=export_customers,
    )

    task_stage_loader = PythonOperator(
        task_id="copy_raw_to_stage_with_validation",
        python_callable=stage_loader_main,
    )

    task_upload_products >> task_export_customers >> task_stage_loader
