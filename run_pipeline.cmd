@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo [1/8] 🚀 Запуск контейнеров через docker-compose...
docker-compose -f infrastructure/docker-compose.yml up --build -d
timeout /t 10

echo [2/8] 📦 Создание Kafka-топика purchases...
docker-compose -f infrastructure/docker-compose.yml exec kafka kafka-topics ^
  --create --topic purchases --bootstrap-server localhost:9092 ^
  --partitions 1 --replication-factor 1 --if-not-exists

echo [3/8] 📨 Отправка сообщений в Kafka...
docker-compose -f infrastructure/docker-compose.yml exec kafka bash -c "echo '{\"customer_id\": 123, \"product_id\": 456, \"seller_id\": 789, \"quantity\": 3, \"price_at_time\": 29.99, \"purchased_at\": \"2025-05-31T15:30:00\"}' | kafka-console-producer --topic purchases --bootstrap-server localhost:9092"

docker-compose -f infrastructure/docker-compose.yml exec kafka bash -c "echo '{\"customer_id\": 42, \"product_id\": 101, \"seller_id\": 55, \"quantity\": 1, \"price_at_time\": 149.99, \"purchased_at\": \"2025-05-31T18:45:22\"}' | kafka-console-producer --topic purchases --bootstrap-server localhost:9092"

docker-compose -f infrastructure/docker-compose.yml exec kafka bash -c "echo '{\"customer_id\": 7, \"product_id\": 2048, \"seller_id\": 16, \"quantity\": 5, \"price_at_time\": 9.99, \"purchased_at\": \"2025-05-31T22:10:37\"}' | kafka-console-producer --topic purchases --bootstrap-server localhost:9092"

echo [4/8] 🛢️ Выгрузка PostgreSQL -> S3...
docker-compose -f infrastructure/docker-compose.yml exec api bash -c "export PYTHONPATH=/app && python /app/data_ingestion/postgres_to_s3.py"

echo [5/8] 🔄 Запуск Spark-стриминга Kafka -> S3...
docker-compose -f infrastructure/docker-compose.yml exec spark-master bash -c "pip install minio && export PYTHONPATH=/app && spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4,org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.3 /app/data_ingestion/kafka_to_s3.py"

echo [6/8] 📤 Загрузка products.parquet в S3...
docker-compose -f infrastructure/docker-compose.yml exec api bash -c "export PYTHONPATH=/app && python /app/data_ingestion/upload_to_s3.py /app/data_ingestion/products.parquet"

echo [7/8] 🧹 Загрузка STAGE слоя...
docker-compose -f infrastructure/docker-compose.yml exec api bash -c "export PYTHONPATH=/app && python /app/data_ingestion/s3_stage_loader.py"

echo [8/8] ✅ Все шаги завершены!
pause
