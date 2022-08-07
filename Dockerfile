FROM python:3.9

RUN mkdir /Usagi
WORKDIR /Usagi
ADD . /Usagi/
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "-u", "/Usagi/main.py"]