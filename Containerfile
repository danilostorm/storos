ARG BASE_IMAGE=ghcr.io/ublue-os/ucore-hci:stable
FROM ${BASE_IMAGE}
ARG STOROS_REVISION=development
LABEL org.opencontainers.image.title="StorOS development base" \
      org.opencontainers.image.source="https://github.com/danilostorm/storos" \
      org.opencontainers.image.revision="${STOROS_REVISION}"
COPY scripts/collect_host.py /usr/libexec/storos/collect_host.py
COPY image/check-image.sh /usr/libexec/storos/check-image.sh
COPY image/storos-release /usr/share/storos/release
RUN bash /usr/libexec/storos/check-image.sh
