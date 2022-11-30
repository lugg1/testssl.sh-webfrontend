FROM alpine:3.17.0

RUN apk update && \
    apk upgrade && \
    apk add bash procps drill git coreutils libidn curl socat openssl aha python3 py3-pip && \
    rm -rf /var/cache/apk/* && \
    addgroup testssl && \
    adduser -G testssl -g "testssl user"  -s /bin/bash -D testssl && \
    mkdir -m 755 -p /home/testssl/etc /home/testssl/bin /home/testssl/app/testssl.sh /home/testssl/app/templates /home/testssl/app/static /home/testssl/app/result/html /home/testssl/app/result/json /home/testssl/app/log && \
    chown testssl:testssl /home/testssl/app/result/html /home/testssl/app/result/json /home/testssl/app/log && \
    ln -s /home/testssl/testssl.sh /usr/local/bin/ && \
    ln -s /home/testssl/testssl.sh /home/testssl/app/testssl.sh/

USER testssl
WORKDIR /home/testssl/app/

COPY --chown=testssl:testssl testssl.sh/etc/. /home/testssl/etc/
COPY --chown=testssl:testssl testssl.sh/bin/. /home/testssl/bin/
COPY --chown=testssl:testssl testssl.sh/testssl.sh  /home/testssl/
COPY --chown=testssl:testssl static/. /home/testssl/app/static/
COPY --chown=testssl:testssl templates/. /home/testssl/app/templates/
COPY --chown=testssl:testssl SSLTestPortal.py /home/testssl/app/
COPY --chown=testssl:testssl requirements.txt /home/testssl/app/

RUN pip install -r /home/testssl/app/requirements.txt

EXPOSE 8080/tcp
ENTRYPOINT ["/home/testssl/.local/bin/gunicorn"]
CMD ["--bind","0.0.0.0:8080","--timeout","300","--workers","4","SSLTestPortal"]
