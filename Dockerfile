# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12-alpine

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
COPY production_additional_requirements.txt .

RUN python -m pip install -U pip wheel
RUN python -m pip install -r requirements.txt
RUN python -m pip install -r production_additional_requirements.txt

COPY . /app
WORKDIR /app
RUN mkdir static
RUN chmod +x entrypoint.sh

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["./entrypoint.sh"]