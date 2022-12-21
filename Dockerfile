FROM python:3.8.14-bullseye

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.2.1

RUN mkdir /project
WORKDIR /project

# Install additional requirements
COPY poetry.lock pyproject.toml /project/

# System deps:
RUN pip install "poetry==$POETRY_VERSION"

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi

# Create venv for target-jsonl (Incompatible dependencies with meltano sdk)
RUN python3 -m venv /opt/venvjsonl/
RUN . /opt/venvjsonl/bin/activate && pip install target-jsonl && chmod -R 755 /opt/venvjsonl/ && mkdir /project/output

# Copy over remaining project files
COPY . /project/

ENTRYPOINT ["/project/docker-pipeline.sh"]