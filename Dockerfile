# install python
FROM python:3.11

# set-up folder
RUN mkdir /Usagi
WORKDIR /Usagi
ADD . /Usagi/

# install bot requirements
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install ffmpeg -y

CMD ["python", "-u", "main.py"]