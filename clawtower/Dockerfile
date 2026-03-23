FROM python:3.12-slim
WORKDIR /app
RUN pip install flask flask-cors gunicorn
COPY server.py .
COPY index.html .
EXPOSE 3000
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:3000"]
