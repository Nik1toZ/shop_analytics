# file: utils/s3_client.py

import os
from minio import Minio
from minio.error import S3Error

def get_s3_client():
    """
    Возвращает экземпляр Minio-клиента, используя переменные окружения:
      MINIO_ENDPOINT, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD
    """
    # Читаем из переменных окружения
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

    # Если в MINIO_ENDPOINT содержится "http://", убираем префикс
    # (Minio() ожидает хост:порт без "http://").
    if endpoint.startswith("http://"):
        endpoint_clean = endpoint.replace("http://", "")
    elif endpoint.startswith("https://"):
        endpoint_clean = endpoint.replace("https://", "")
    else:
        endpoint_clean = endpoint

    # Создаём Minio-клиент
    try:
        client = Minio(
            endpoint_clean,
            access_key=access_key,
            secret_key=secret_key,
            secure=False  # ставим False, т.к. обычно MinIO в dev-среде без TLS
        )
        return client
    except S3Error as err:
        print("Error initializing MinIO client:", err)
        raise
