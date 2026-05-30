import os
import io
import json
import re
import boto3
from datetime import datetime
from dotenv import load_dotenv
from .config import CrawlerConfig
from .spider import TopCVSpider

load_dotenv()

def extract_job_id(url):
    match = re.search(r'/(\d+)\.html', url)
    return match.group(1) if match else None

def run() -> None:
    config = CrawlerConfig()
    spider = TopCVSpider(config)

    items = spider.crawl()
    crawl_time = datetime.now().isoformat()

    for item in items:
        item["crawl_time"] = crawl_time
        item["job_id"] = extract_job_id(item["job_url"])

    # 1. Khởi tạo S3 Client (Dùng cho AWS S3)
    s3_client = boto3.client(
        's3',
        region_name='us-east-1',
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
    )

    bucket = 'amzn-s3-job-prj'

    # 2. Convert list -> jsonl string
    jsonl_data = "\n".join(json.dumps(item, ensure_ascii=False) for item in items)
    data_bytes = jsonl_data.encode("utf-8") # Chuyển sang bytes trực tiếp

    # Định dạng path: raw/topcv_jobs/dt=2026-04-29/20260429_154500.jsonl
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    object_key = f"raw/topcv_jobs/dt={today}/{timestamp}.jsonl"

    # 3. Upload lên S3 dùng put_object của boto3
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=object_key,
            Body=data_bytes,
            ContentType="application/json"
        )
        print(f"Uploaded {len(items)} jobs to S3: {object_key}")
    except Exception as e:
        print(f"Error uploading to S3: {e}")

if __name__ == "__main__":
    run()