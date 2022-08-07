FROM python:3.9

RUN mkdir /Usagi
WORKDIR /Usagi
ADD . /Usagi/
RUN pip install -r requirements.txt

RUN apt-get update && apt-get install ffmpeg -y

COPY . .

CMD ["python3", "-u", "/Usagi/main.py"]