from __future__ import annotations

import pendulum

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG


PROJECT_DIR = "/opt/airflow/project"
DBT_PROJECT_DIR = f"{PROJECT_DIR}/topcv_dbt"
DBT_PROFILES_DIR = "/opt/airflow/config/dbt"
NOTEBOOK_OUTPUT_DIR = "/opt/airflow/logs/notebooks"


with DAG(
    dag_id="topcv_job_pipeline",
    description="Crawl TopCV data, build Bronze/Silver Iceberg tables, and build dbt marts.",
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Ho_Chi_Minh"),
    schedule="0 1 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["job-ete", "topcv", "dbt"],
) as dag:
    crawl_topcv_to_s3 = BashOperator(
        task_id="crawl_topcv_to_s3",
        bash_command="python -m pipelines.ingestion.craw_data.run",
        cwd=PROJECT_DIR,
        append_env=True,
    )

    run_bronze_notebook = BashOperator(
        task_id="run_bronze_notebook",
        bash_command=(
            f"mkdir -p {NOTEBOOK_OUTPUT_DIR} && "
            f"papermill {PROJECT_DIR}/pipelines/spark_jobs/bronze.ipynb "
            f"{NOTEBOOK_OUTPUT_DIR}/bronze_{{{{ ts_nodash }}}}.ipynb"
        ),
        cwd=PROJECT_DIR,
        append_env=True,
    )

    run_silver_notebook = BashOperator(
        task_id="run_silver_notebook",
        bash_command=(
            f"mkdir -p {NOTEBOOK_OUTPUT_DIR} && "
            f"papermill {PROJECT_DIR}/pipelines/spark_jobs/silver.ipynb "
            f"{NOTEBOOK_OUTPUT_DIR}/silver_{{{{ ts_nodash }}}}.ipynb"
        ),
        cwd=PROJECT_DIR,
        append_env=True,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            "dbt run "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR} "
            '--target "${DBT_TARGET:-dev}"'
        ),
        cwd=PROJECT_DIR,
        append_env=True,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "dbt test "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR} "
            '--target "${DBT_TARGET:-dev}"'
        ),
        cwd=PROJECT_DIR,
        append_env=True,
    )

    crawl_topcv_to_s3 >> run_bronze_notebook >> run_silver_notebook >> dbt_run >> dbt_test
