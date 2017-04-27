FROM fernandosanchez/appstudio:alpine-python3

RUN mkdir -p src
COPY ./src/* ./
RUN pip install -r requirements.txt
ENTRYPOINT python3 -u actor.py
