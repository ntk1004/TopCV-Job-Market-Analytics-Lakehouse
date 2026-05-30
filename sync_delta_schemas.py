#!/usr/bin/env python3
"""
Auto-sync Delta table schemas to AWS Glue Catalog
Run this script periodically to keep Glue Catalog in sync with Delta tables
"""

import sys
import os
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system env vars

# Add project paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'pipelines'))

from pyspark.sql import SparkSession
from utils.glue_catalog import GlueCatalogManager


def create_spark_session():
    """Create Spark session with Delta and Glue support"""
    return SparkSession.builder \
        .appName("delta-schema-sync") \
        .master("local[*]") \
        .config("spark.jars.packages",
            "io.delta:delta-spark_2.12:3.1.0,"
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.262"
        ) \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.hadoop.fs.s3a.endpoint", "s3.us-east-1.amazonaws.com") \
        .config("spark.hadoop.fs.s3a.access.key", os.environ.get('aws_access_key_id', '')) \
        .config("spark.hadoop.fs.s3a.secret.key", os.environ.get('aws_secret_access_key', '')) \
        .config("spark.hadoop.fs.s3a.path.style.access", "false") \
        .config("spark.hadoop.hive.metastore.client.factory.class",
                "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory") \
        .config("spark.sql.warehouse.dir", "s3a://amzn-s3-job-prj/warehouse/") \
        .enableHiveSupport() \
        .getOrCreate()


def main():
    """Main function to sync all Delta table schemas"""
    print(f"🔄 Starting schema sync at {datetime.now()}")

    # Initialize Spark and Glue Manager
    spark = create_spark_session()
    glue_mgr = GlueCatalogManager(
        spark=spark,
        region='us-east-1',
        aws_access_key_id=os.environ.get('aws_access_key_id'),
        aws_secret_access_key=os.environ.get('aws_secret_access_key')
    )

    # Configuration
    database_name = 'job_ete_catalog'
    tables_to_sync = [
        ('topcv_jobs_bronze', 's3a://amzn-s3-job-prj/bronze/topcv_jobs'),
        ('topcv_jobs_silver', 's3a://amzn-s3-job-prj/silver/topcv_jobs'),
        ('topcv_jobs_gold', 's3a://amzn-s3-job-prj/gold/topcv_jobs')
    ]

    # Sync all tables
    success_count = 0
    for table_name, s3_location in tables_to_sync:
        print(f"\n📊 Syncing {table_name}...")
        if glue_mgr.sync_delta_schema_to_glue(database_name, table_name, s3_location):
            success_count += 1
        else:
            print(f"❌ Failed to sync {table_name}")

    # Summary
    print(f"\n✅ Sync completed: {success_count}/{len(tables_to_sync)} tables updated")
    print(f"🏁 Finished at {datetime.now()}")

    # Stop Spark
    spark.stop()


if __name__ == "__main__":
    main()