FROM python:3.7

VOLUME ['/code']
WORKDIR /code

COPY requirements.txt /code

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

CMD python3 run_page_and_detail.py
