FROM python:3.9-slim

COPY requirements.txt /tmp/
COPY ./app /app
COPY ./scripts /scripts
WORKDIR "/app"

RUN pip install -r /tmp/requirements.txt

EXPOSE 8050

ENTRYPOINT [ "python3" ]
CMD [ "dash_app.py" ]
