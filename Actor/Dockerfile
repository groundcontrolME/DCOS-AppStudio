FROM frolvlad/alpine-python3
COPY requirements.txt .
COPY actor.py .
RUN pip install -r requirements.txt
CMD python3 -u actor.py
