ARG BASE_IMAGE=ghcr.io/ublue-os/ucore-hci@sha256:7dbb268b3d556e8bfa95bb922185c6a2ad9f580896bf25c6d3a81df541732464
FROM ${BASE_IMAGE}
ARG STOROS_REVISION=development
LABEL org.opencontainers.image.title="StorOS development base" \
      org.opencontainers.image.source="https://github.com/danilostorm/storos" \
      org.opencontainers.image.revision="${STOROS_REVISION}"
COPY scripts/collect_host.py /usr/libexec/storos/collect_host.py
COPY image/check-image.sh /usr/libexec/storos/check-image.sh
COPY image/storos-release /usr/share/storos/release
RUN bash /usr/libexec/storos/check-image.sh
