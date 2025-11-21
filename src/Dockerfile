FROM python:3.13-slim-bullseye
EXPOSE 80

RUN apt update -y && apt install -y iproute2 ssh && apt clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*



COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN mkdir -p -m 0700 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

WORKDIR /home/user/application
COPY . /home/user/application

RUN uv sync --dev

CMD ["/home/user/application/start.sh"]
