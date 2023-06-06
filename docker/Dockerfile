FROM python:3.11-slim
WORKDIR /app

RUN pip install supervisor

# install PDM
RUN pip install -U pip setuptools wheel
RUN pip install pdm==2.4.0

COPY pyproject.toml pdm.lock ./
RUN pdm install --prod --no-lock --no-editable

COPY ./docker/supervisord.conf /etc/supervisord.conf
COPY ./docker/supervisord.conf.d /etc/supervisor/conf.d
COPY . .

ENTRYPOINT ["./docker/entrypoints/entrypoint.sh"]
