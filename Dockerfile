<<<<<<< HEAD
FROM python:3.8

RUN mkdir /Usagi
WORKDIR /Usagi
ADD . /Usagi/
RUN pip install -r requirements.txt

CMD ["python3", "/Usagi/main.py"]
=======
FROM python:3.8

RUN mkdir /Usagi
WORKDIR /Usagi
ADD . /Usagi/
RUN pip install -r requirements.txt

CMD ["python3", "/Usagi/main.py"]
>>>>>>> 634de8221c8463b8d4006242546d580dcbf536ea
