ARG BUILD_FROM
FROM $BUILD_FROM

ENV \
    S6_SERVICES_GRACETIME=10000 \
    SUPERVISOR_API=http://localhost

# Install base
RUN \
    apk add --no-cache \
        eudev \
        eudev-libs \
        git \
        glib \
        libffi \
        libpulse \
        musl \
        openssl

ARG BUILD_ARCH
WORKDIR /usr/src

# Install requirements
COPY requirements.txt .
RUN \
    export MAKEFLAGS="-j$(nproc)" \
    && pip3 install --no-cache-dir --no-index --only-binary=:all: --find-links \
        "https://openpeerpower.io/whl-ix/alpine-$(cut -d '.' -f 1-2 < /etc/alpine-release)/${BUILD_ARCH}/" \
        -r ./requirements.txt \
    && rm -f requirements.txt

# Install Open Peer Power Supervisor
COPY . supervisor
RUN \
    pip3 install --no-cache-dir -e ./supervisor \
    && python3 -m compileall ./supervisor/supervisor


WORKDIR /
COPY rootfs /
