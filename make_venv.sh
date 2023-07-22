cd app

python3 -m venv venvpi
ls
ls ./venvpi
source ./venvpi/bin/activate
pip install -r requirements.txt

# docker run -it --rm --mount type=bind,source="$(pwd)",target=/app/ python:3.11 bash ./app/make_venv.sh