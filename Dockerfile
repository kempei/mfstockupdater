FROM python:3.9.6-alpine3.14

# update apk repo
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.13/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.13/community" >> /etc/apk/repositories

# install chromedriver
RUN apk add --update --no-cache \
        chromium chromium-chromedriver \
        libffi-dev

ARG project_dir=/tmp/work
RUN mkdir $project_dir
ADD requirements.txt $project_dir
WORKDIR $project_dir

RUN pip install --upgrade pip; \
    pip install -r requirements.txt; \
    find /usr/local -depth \
		\( \
			\( -type d -a \( -name test -o -name tests \) \) \
			-o \
			\( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
		\) -exec rm -rf '{}' +; \
	rm -f get-pip.py

ADD mf.py $project_dir

CMD [ "python", "-u", "/tmp/work/mf.py" ]
