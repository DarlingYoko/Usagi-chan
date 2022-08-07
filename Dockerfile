FROM python:3.9

RUN mkdir /Usagi
WORKDIR /Usagi
ADD . /Usagi/
RUN pip install -r requirements.txt

RUN set -x \
    && add-apt-repository ppa:mc3man/trusty-media \
    && apt-get update \
    && apt-get dist-upgrade \
    && apt-get install -y --no-install-recommends \
        ffmpeg

COPY . .

CMD ["python3", "-u", "/Usagi/main.py"]