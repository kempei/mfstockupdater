FROM joyzoursky/python-chromedriver:3.7-alpine3.8-selenium

RUN pip install --upgrade pip; \
    pip install logzero requests pytz; \
    find /usr/local -depth \
		\( \
			\( -type d -a \( -name test -o -name tests \) \) \
			-o \
			\( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
		\) -exec rm -rf '{}' +; \
	rm -f get-pip.py
RUN mkdir /tmp/work
ADD mf.py /tmp/work/

CMD [ "python", "-u", "/tmp/work/mf.py" ]
