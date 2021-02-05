FROM python:3.9-slim

WORKDIR /app
ENV PATH=/root/.local/bin:$PATH

COPY requirements.txt .
RUN pip install --user -r requirements.txt

COPY main.py .
CMD [ "python", "main.py" ]
