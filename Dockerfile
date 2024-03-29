FROM python:3.11.4-alpine3.18

# update apk repo
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.18/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.18/community" >> /etc/apk/repositories

ARG project_dir=/tmp/work
RUN mkdir $project_dir
ADD requirements.txt $project_dir
WORKDIR $project_dir

RUN apk add --no-cache --virtual .build-deps \
    gcc \
    python3-dev \
    musl-dev \
    libffi-dev \
    build-base && \
    apk add --no-cache \
    chromium \
    chromium-chromedriver && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del --no-cache .build-deps && \
    find /usr/local -depth \
    \( \
    \( -type d -a \( -name test -o -name tests \) \) \
    -o \
    \( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
    \) -exec rm -rf '{}' + && \
    rm -f get-pip.py && \
    rm -Rf /root/.cache/

ADD mf.py $project_dir

CMD [ "python", "-u", "/tmp/work/mf.py" ]
