# Kien truc crawler TopCV (Selenium + Parser)

## Muc tieu
- Crawl danh sach job tu TopCV voi trang co render JS.
- Tach rieng cac thanh phan de de mo rong va test.

## Cau truc
- `config.py`: cau hinh crawl (`base_url`, `max_pages`, timeout, output path).
- `browser.py`: tao va cau hinh Chrome WebDriver.
- `spider.py`: dieu phoi crawl theo tung trang bang Selenium, lay danh sach card viec lam.
- `parser.py`: lay link tu card, parse trang chi tiet job (`parse_job_detail`).
- `models.py`: mo hinh du lieu job.
- `storage.py`: ghi du lieu ra JSONL.
- `run.py`: entrypoint chay crawl end-to-end.

## Luong xu ly
1. `run.py` tao `CrawlerConfig`.
2. `run.py` khoi chay spider `TopCVSpider`.
3. Spider dung Selenium mo URL tung trang, doi danh sach card load xong.
4. Voi moi link job: mo trang chi tiet, lay title/company/location/salary/skills.
5. `save_jsonl` ghi du lieu vao `output/topcv_jobs.jsonl`.

## Chay thu
```bash
python -m pipelines.ingestion.craw_data.run
```

## Luu y
- CSS selector cua TopCV co the thay doi theo thoi gian, can cap nhat trong `spider.py` va `parser.py`.
- TopCV co anti-bot, nen nen giu user-agent hop ly va can nhac them delay/retry neu bi block.

