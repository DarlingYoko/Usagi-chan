# install python
FROM python:3.12

# ffmpeg for the Music cog; first so code changes don't bust this layer
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home usagi

WORKDIR /Usagi

# install bot requirements before copying code for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=usagi:usagi . .
# the bot writes runtime files (tempMusic, yt-dlp downloads) under the workdir
RUN chown usagi:usagi /Usagi

USER usagi

CMD ["python", "-u", "main.py"]
