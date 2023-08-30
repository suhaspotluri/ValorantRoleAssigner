FROM python:3.11

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY ./src ./src

CMD ["python3", "src/main.py"]
