ARG AIRFLOW_VERSION=3.2.2
ARG PYTHON_VERSION=3.10

FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}

ARG AIRFLOW_VERSION

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        curl \
        openjdk-17-jre-headless \
        procps \
    && install -o airflow -g 0 -m 775 /usr/bin/chromedriver /usr/local/bin/chromedriver-undetected \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/local/bin/chromedriver-undetected \
    PYSPARK_DRIVER_PYTHON=python \
    PYSPARK_PYTHON=python

USER airflow

COPY airflow/requirements.txt /tmp/job_ete_airflow_requirements.txt
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /tmp/job_ete_airflow_requirements.txt
