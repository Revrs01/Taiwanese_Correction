FROM python:3.10.14
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

RUN apt update && apt install -y vim curl supervisor

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]
