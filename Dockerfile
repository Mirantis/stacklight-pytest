FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive \
    DEBCONF_NONINTERACTIVE_SEEN=true \
    LANG=C.UTF-8 \
    LANGUAGE=$LANG
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER root

WORKDIR /stacklight-pytest

COPY . ./

# runtime deps
RUN apt-get update \
 && apt-get -y upgrade \
 && apt-get -y --no-install-recommends install \
      curl \
      git-core \
      iputils-ping \
      libffi6 \
      libldap-2.4-2 \
      libsasl2-2 \
      libssl1.0.0 \
      patch \
      python \
      python2.7 \
      vim-tiny \
      virtualenv \
      wget

# build
RUN set -ex; \
    buildDeps="build-essential libffi-dev libldap2-dev libsasl2-dev libssl-dev python-pip"; \
    apt-get install -y --no-install-recommends ${buildDeps} \
 && curl -L https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl \
 && chmod a+x /usr/local/bin/kubectl \
 && python -m pip install --upgrade 'pip==9.0.3' \
 && virtualenv venv \
 && . venv/bin/activate \
 && pip install . \
 && pip install -r requirements.txt \
 && apt-get -y --autoremove purge ${buildDeps} \
 && apt-get -y clean \
 && rm -rf \
      /root/.cache \
      /var/lib/apt/lists/* \
      /tmp/* \
      /var/tmp/* \
      /etc/apt/sources.list.d/* \
 && echo > /etc/apt/sources.list

CMD ./entrypoint.sh
