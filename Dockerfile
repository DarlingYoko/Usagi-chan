FROM python:3.11

RUN mkdir /Usagi
WORKDIR /Usagi
ADD . /Usagi/

#RUN pip install -r requirements.txt

RUN apt-get update && apt-get install ffmpeg -y

CMD ["./venvpi/bin/python", "-u", "main.py"]