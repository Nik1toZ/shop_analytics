# data_ingestion/s3_stage_loader.py

import os
from minio import Minio
from pyarrow.parquet import ParquetFile


def list_objects_in_bucket(s3_client, bucket_name, prefix=""):
    """Возвращает список имен объектов (keys) в бакете."""
    items = []
    for obj in s3_client.list_objects(bucket_name, prefix=prefix, recursive=True):
        items.append(obj.object_name)
    return items

def validate_parquet(s3_client, bucket_name, object_key):
    """
    Проверяет, что файл существует и имеет корректный Parquet-формат.
    Можно скачать первые N байт и проверить PyArrow.
    """
    # Скачиваем небольшой кусочек
    try:
        response = s3_client.get_object(bucket_name, object_key)
        pf = ParquetFile(response)  # если не Parquet, упадёт исключение
        return True
    except Exception as e:
        print(f"❌ Validation error for {bucket_name}/{object_key}: {e}")
        return False

def copy_object(s3_client, source_bucket, source_key, dest_bucket, dest_key):
    """Копирует объект из одного бакета в другой."""
    # Если нет dest_bucket, создаём
    if not s3_client.bucket_exists(dest_bucket):
        s3_client.make_bucket(dest_bucket)

    # Делаем copy
    copy_src = {'Bucket': source_bucket, 'Key': source_key}
    s3_client.copy_object(
        bucket_name=dest_bucket,
        object_name=dest_key,
        object_source=copy_src
    )
    print(f"Copied {source_bucket}/{source_key} → {dest_bucket}/{dest_key}")

def main():
    s3_client = Minio(
        os.getenv("MINIO_ENDPOINT", "minio:9000").replace("http://", "").replace("https://", ""),
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
        secure=False
    )
    # Предполагаем, что все сырые данные лежат в bucket = shop-raw-data
    source_bucket = os.getenv("S3_BUCKET_RAW", "shop-raw-data")
    # А bucket Stage = shop-stage-data
    dest_bucket = os.getenv("S3_BUCKET_STAGE", "shop-stage-data")

    # 1. Список директорий в raw:
    prefixes = ["customers/", "purchases/", "products/"]  # т.е. папки для разных типов данных

    for prefix in prefixes:
        keys = list_objects_in_bucket(s3_client, source_bucket, prefix=prefix)
        for key in keys:
            # 2. Проверяем Parquet
            if key.endswith(".parquet"):
                if validate_parquet(s3_client, source_bucket, key):
                    # Формируем путь назначения (например, просто копируем ту же структуру)
                    dest_key = key.replace(prefix, prefix)  # можно оставить тот же prefix
                    copy_object(s3_client, source_bucket, key, dest_bucket, dest_key)
            else:
                print(f"Skipping non-parquet file: {key}")

if __name__ == "__main__":
    main()
