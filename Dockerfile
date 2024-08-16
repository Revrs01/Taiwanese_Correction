FROM python:3.10.14
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

RUN apt update && apt install -y vim cron curl supervisor
COPY cronjob /etc/cron.d/cronjob
RUN chmod 0644 /etc/cron.d/cronjob
RUN crontab /etc/cron.d/cronjob
RUN touch /var/log/cron.log

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]