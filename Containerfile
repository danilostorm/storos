ARG BASE_IMAGE=ghcr.io/ublue-os/ucore-hci@sha256:7dbb268b3d556e8bfa95bb922185c6a2ad9f580896bf25c6d3a81df541732464
FROM ${BASE_IMAGE}
ARG STOROS_REVISION=development
LABEL org.opencontainers.image.title="StorOS development base" \
      org.opencontainers.image.source="https://github.com/danilostorm/storos" \
      org.opencontainers.image.revision="${STOROS_REVISION}"
COPY scripts/collect_host.py /usr/libexec/storos/collect_host.py
COPY src/storos_agent.py /usr/libexec/storos/storos_agent.py
COPY bin/storosctl /usr/bin/storosctl
COPY image/storos-agent.service /usr/lib/systemd/system/storos-agent.service
COPY image/check-image.sh /usr/libexec/storos/check-image.sh
COPY image/storos-release /usr/share/storos/release
RUN chmod 0755 /usr/bin/storosctl && systemctl enable storos-agent.service && bash /usr/libexec/storos/check-image.sh
