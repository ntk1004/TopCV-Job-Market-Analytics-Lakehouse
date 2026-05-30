# Auto-sync Delta schemas to Glue Catalog every 6 hours
cd /mnt/k/job_ete && source .venv/bin/activate && python3 sync_delta_schemas.py >> sync_log.txt 2>&1
