# job-ete

Local data stack for crawling TopCV jobs, syncing Delta schemas, and running dbt models through Apache Airflow on Docker.

## Environment

Create `.env` in the repo root. Start from `.env.example` and fill the AWS values:

```bash
cp .env.example .env
```

Required values for the pipeline:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`
- `DBT_ATHENA_S3_STAGING_DIR`
- `DBT_ATHENA_S3_DATA_DIR`

On Windows, keep `AIRFLOW_UID=50000`.

## Run Airflow With Docker

Run commands from the repo root:

```bash
docker compose --env-file .env -f infrastructure/docker/docker-compose.yml up --build airflow-init
docker compose --env-file .env -f infrastructure/docker/docker-compose.yml up -d
```

Airflow UI:

- URL: http://localhost:8080
- Username: `airflow`
- Password: `airflow`

The DAG is `topcv_job_pipeline`. It is paused on creation; unpause it in the UI or trigger it manually.

Pipeline order:

```text
crawl_topcv_to_s3 -> run_bronze_notebook -> run_silver_notebook -> sync_delta_schemas -> dbt_run -> dbt_test
```

## Useful Commands

```bash
docker compose --env-file .env -f infrastructure/docker/docker-compose.yml ps
docker compose --env-file .env -f infrastructure/docker/docker-compose.yml logs -f airflow-worker
docker compose --env-file .env -f infrastructure/docker/docker-compose.yml run --rm airflow-cli airflow dags list
docker compose --env-file .env -f infrastructure/docker/docker-compose.yml down
```

Clean all local Airflow/Postgres volumes:

```bash
docker compose --env-file .env -f infrastructure/docker/docker-compose.yml down --volumes --remove-orphans
```
