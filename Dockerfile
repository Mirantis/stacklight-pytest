FROM ubuntu:16.04

ENV DEBIAN_FRONTEND=noninteractive \
    DEBCONF_NONINTERACTIVE_SEEN=true \
    LANG=C.UTF-8 \
    LANGUAGE=$LANG
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER root

WORKDIR /kaas-stacklight-pytest

COPY . ./

RUN set -ex; apt-get update && apt-get upgrade -y && \
    apt-get install -y build-essential curl git-core iputils-ping libffi-dev libldap2-dev libsasl2-dev libssl-dev patch python-dev python-pip  vim-tiny wget python-virtualenv

# Install kubectl
RUN curl -L https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl \
    && chmod a+x /usr/local/bin/kubectl

# Enable these packages while porting to Python3  =>  python3-virtualenv python3-dev  \
# Due to upstream bug we should use fixed version of pip
RUN python -m pip install --upgrade 'pip==9.0.3'  \
    && virtualenv venv \
    && . venv/bin/activate \
    && pip install . \
    && pip install -r requirements.txt

# Cleanup
RUN apt-get -y purge libx11-data xauth libxmuu1 libxcb1 libx11-6 libxext6 ppp pppconfig pppoeconf popularity-contest cpp gcc g++ libssl-doc && \
    apt-get -y autoremove; apt-get -y clean ; rm -rf /root/.cache; rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/* ; rm -rf /var/tmp/* ; rm -rfv /etc/apt/sources.list.d/* ; echo > /etc/apt/sources.list

COPY entrypoint.sh /entrypoint.sh

#ENTRYPOINT ["entrypoint.sh"]
# docker build --no-cache -t cvp-sanity-checks:test_latest .
