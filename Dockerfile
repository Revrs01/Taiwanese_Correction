FROM python:3.10.14
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 9083
CMD ["python", "app.py"]