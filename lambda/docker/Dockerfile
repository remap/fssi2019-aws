FROM amazonlinux

RUN yum -y install python3 \
    zip \
    && yum clean all

RUN pip3 install --upgrade pip \
    && pip3 install boto3

COPY package.sh /package.sh
RUN chmod +x /package.sh

CMD /package.sh
