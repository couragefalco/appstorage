FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8501

CMD streamlit run --server.port 8501 --logger.level=debug app.py