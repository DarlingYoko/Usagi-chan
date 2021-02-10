FROM python:3.8

RUN mkdir /Usagi
WORKDIR /Usagi
ADD . /Usagi/
RUN pip install -r requirements.txt

CMD ["python3", "/Usagi/main.py"]
