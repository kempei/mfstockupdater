FROM joyzoursky/python-chromedriver:3.7-alpine3.8-selenium

ARG project_dir=/tmp/work
RUN mkdir $project_dir
ADD mf.py $project_dir
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

CMD [ "python", "-u", "/tmp/work/mf.py" ]
