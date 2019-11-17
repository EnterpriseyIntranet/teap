FROM python:3

RUN true \
        && apt-get update -y \
	&& curl -sL https://deb.nodesource.com/setup_11.x | bash - \
        && apt-get install -y \
                python3-pip python3-dev build-essential gunicorn3 \
                nodejs \
                elinks \
                libldap2-dev libsasl2-dev \
        && apt-get clean all -y \
        && true

WORKDIR /app

# First of all, copy dependencies metadata and install the deps
COPY requirements.txt .
COPY requirements/ requirements/
COPY frontend/package.json frontend/package-lock.json frontend/

RUN true \
	&& pip install -r requirements.txt \
	&& (cd frontend && npm install) \
        && true

# Then, copy all of the rest.
# MAKE SURE THAT YOU HAVE A CLEAN REPOSITORY unles you're in for a surprise
COPY . .

RUN true \
	&& (cd frontend  && npm run build) \
        && true

EXPOSE 8080

# CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8080"]
CMD ["gunicorn", "autoapp:app", "-b", ":8080", "--reload"]
