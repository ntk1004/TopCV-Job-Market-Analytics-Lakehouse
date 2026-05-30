"""
Helper module for AWS Glue Catalog operations with Delta tables
"""
import boto3
from pyspark.sql import SparkSession
from typing import List, Dict, Optional
from botocore.exceptions import ClientError
from datetime import datetime


class GlueCatalogManager:
    """Manage Delta tables in AWS Glue Catalog"""
    
    def __init__(
        self, 
        spark: SparkSession, 
        region: str = 'us-east-1',
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        self.spark = spark
        
        # Setup boto3 client with credentials if provided
        if aws_access_key_id and aws_secret_access_key:
            self.glue_client = boto3.client(
                'glue',
                region_name=region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
        else:
            self.glue_client = boto3.client('glue', region_name=region)
        
    def create_database(self, database_name: str, s3_location: str = '') -> bool:

        try:
            try:
                self.glue_client.get_database(Name=database_name)
                print(f"Database '{database_name}' already exists in Glue Catalog")
                return True
            except self.glue_client.exceptions.EntityNotFoundException:
                self.glue_client.create_database(
                    DatabaseInput={
                        'Name': database_name,
                        'LocationUri': s3_location
                    }
                )
                print(f"Database '{database_name}' created in Glue Catalog")
                return True
        except Exception as e:
            print(f"Error creating database in Glue Catalog: {e}")
            return False

    def register_delta_table(
        self,
        database_name: str,
        table_name: str,
        s3_location: str,
        description: str = ''
    ) -> bool:
        """
        Register a Delta table in Spark/Glue metastore.
        """
        if not self.create_database(database_name):
            return False

        try:
            comment = f"COMMENT '{description}'" if description else ""
            self.spark.sql(f"""
                CREATE TABLE IF NOT EXISTS {database_name}.{table_name}
                USING DELTA
                LOCATION '{s3_location}'
                {comment}
            """)
            print(f"Registered Delta table {database_name}.{table_name}")
            return True
        except Exception as e:
            print(f"Error registering Delta table: {e}")
            return False

    def register_multiple_tables(
        self,
        database_name: str,
        tables_config: List[Dict[str, str]]
    ) -> Dict[str, bool]:
        """
        Register multiple Delta tables at once.
        """
        results = {}
        for config in tables_config:
            name = config['name']
            location = config['location']
            description = config.get('description', '')
            results[name] = self.register_delta_table(
                database_name, name, location, description
            )
        return results

    def list_databases(self) -> None:
        """List all databases in Glue Catalog"""
        print("--- Databases in Glue Catalog ---")
        self.spark.sql("SHOW DATABASES").show(truncate=False)
    
    def list_tables(self, database_name: str) -> None:
        """List all tables in a database"""
        print(f"--- Tables in {database_name} ---")
        self.spark.sql(f"SHOW TABLES IN {database_name}").show(truncate=False)
    
    def describe_table(self, database_name: str, table_name: str) -> None:
        """Show table schema and properties"""
        print(f"--- Schema of {database_name}.{table_name} ---")
        self.spark.sql(
            f"DESCRIBE TABLE {database_name}.{table_name}"
        ).show(truncate=False)
        
    def get_table_metadata(self, database_name: str, table_name: str) -> Dict:
        """Get table metadata from Glue"""
        try:
            response = self.glue_client.get_table(
                DatabaseName=database_name,
                Name=table_name
            )
            return response['Table']
        except ClientError as e:
            print(f"✗ Error getting table metadata: {e}")
            return {}

    def sync_delta_schema_to_glue(
        self,
        database_name: str,
        table_name: str,
        s3_location: str
    ) -> bool:
        """Sync schema from a Delta table stored in S3 to Glue Catalog."""
        try:
            if not self.create_database(database_name):
                print(f"Error ensuring database {database_name} exists")
                return False
            # Ensure Spark/Glue metastore is aware of the Delta table location.
            if not self.spark.catalog.tableExists(f"{database_name}.{table_name}"):
                self.spark.sql(f"""
                    CREATE TABLE IF NOT EXISTS {database_name}.{table_name}
                    USING DELTA
                    LOCATION '{s3_location}'
                """)
                print(f"✓ Registered Delta table {database_name}.{table_name}")
                return True
            else:
                self.spark.catalog.refreshTable(f"{database_name}.{table_name}")
                print(f"✓ Table {database_name}.{table_name} refreshed")
                return True
        except Exception as e:
            print(f"✗ Error syncing schema for {table_name}: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Initialize (you need a Spark session)
    # glue_mgr = GlueCatalogManager(spark)
    
    # Create database
    # glue_mgr.create_database('my_database', 'My data catalog')
    
    # Register single table
    # glue_mgr.register_delta_table(
    #     'my_database',
    #     'my_table',
    #     's3a://bucket/path/to/delta',
    #     'Table description'
    # )
    
    # Register multiple tables
    # tables = [
    #     {'name': 'table1', 'location': 's3a://bucket/path1', 'description': 'Table 1'},
    #     {'name': 'table2', 'location': 's3a://bucket/path2', 'description': 'Table 2'},
    # ]
    # glue_mgr.register_multiple_tables('my_database', tables)
    
    pass
