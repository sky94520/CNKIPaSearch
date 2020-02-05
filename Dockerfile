FROM python:3.7

VOLUME ['/code']
WORKDIR /code

COPY requirements.txt /code

RUN pip install -r requirements.txt

CMD python3 run_page.py
