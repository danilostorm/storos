ARG BASE_IMAGE=ghcr.io/ublue-os/ucore-hci@sha256:7dbb268b3d556e8bfa95bb922185c6a2ad9f580896bf25c6d3a81df541732464
FROM ${BASE_IMAGE}
ARG STOROS_REVISION=development
LABEL org.opencontainers.image.title="StorOS development base" \
      org.opencontainers.image.source="https://github.com/danilostorm/storos" \
      org.opencontainers.image.revision="${STOROS_REVISION}"
COPY scripts/collect_host.py /usr/libexec/storos/collect_host.py
COPY src/storos_agent.py /usr/libexec/storos/storos_agent.py
COPY src/storos_config.py /usr/libexec/storos/storos_config.py
COPY src/storos_vm.py /usr/libexec/storos/storos_vm.py
COPY src/storos_vm_store.py /usr/libexec/storos/storos_vm_store.py
COPY src/storos_fingerprints.py /usr/libexec/storos/storos_fingerprints.py
COPY src/storos_tasks.py /usr/libexec/storos/storos_tasks.py
COPY src/storos_preflight.py /usr/libexec/storos/storos_preflight.py
COPY src/storos_execution_contract.py /usr/libexec/storos/storos_execution_contract.py
COPY src/storos_cli.py /usr/libexec/storos/storos_cli.py
COPY src/storos_web.py /usr/libexec/storos/storos_web.py
COPY bin/storosctl /usr/bin/storosctl
COPY image/storos-agent.service /usr/lib/systemd/system/storos-agent.service
COPY image/storos-web.service /usr/lib/systemd/system/storos-web.service
COPY image/10-storos.preset /usr/lib/systemd/system-preset/10-storos.preset
COPY image/check-image.sh /usr/libexec/storos/check-image.sh
COPY image/storos-release /usr/share/storos/release
COPY image/storos-disk.yaml /usr/lib/image-builder/bootc/disk.yaml
RUN chmod 0755 /usr/bin/storosctl \
    && PYTHONPATH=/usr/libexec/storos python3 -c "from storos_execution_contract import execution_contract,backend_capabilities,authorization_decision; c=execution_contract(); b=backend_capabilities(); assert c['executable'] is False and c['worker_available'] is False and c['feature_gate_may_enable_write'] is False; assert b['mutating_available'] is False and all(v['supported'] is False for v in b['actions'].values()); assert authorization_decision('image-smoke','start_vm','11111111-2222-3333-4444-555555555555')['granted'] is False" \
    && systemctl preset storos-agent.service storos-web.service \
    && bash /usr/libexec/storos/check-image.sh
