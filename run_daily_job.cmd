@echo off
echo Starting daily Spark ETL job...

docker-compose -f infrastructure/docker-compose.yml exec spark-master bash /app/run_daily_job.sh

echo Job finished.
