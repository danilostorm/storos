# StorOS v0.5 USB preview: status and safe verification

## Actual status

- Sources from StorOS main assembled with the latest navigation, storage, Main disk grouping, module inventories and local XML-to-Compose importer.
- Existing Fedora 44 BuildLab started; source archive copied into its home directory.
- All 61 tests passed on the AEROCOOL and in the Fedora BuildLab before the build attempt.
- Installer files: installer/Containerfile.ui-v05 and installer/build-ui-v05.sh.
- Executing the remote image build was blocked by the connected tool's security controls. **No v0.5 RAW/IMG has been built, transferred or boot-tested yet.**
- Graceful shutdown was requested for BuildLab after the tests. The prior v0.4 IMG and all registered VM disk images were preserved.

## Legacy BIOS: verified observations

QEMU/SeaBIOS used disposable QCOW2 overlays on the v0.4 USB IMG:
- Legacy firmware found the bootloader, started the Linux kernel and early systemd with 768 MiB RAM in the first test.
- A second test with 3 GiB RAM and 2 vCPU reached the StorOS graphical Firefox kiosk. The dashboard rendered real CPU, memory and storage values. The test used a temporary overlay and isolated QEMU with no network or physical disks.
- The same v0.4 IMG previously reached the GUI under UEFI/OVMF. Therefore both QEMU firmware modes have reached the GUI on v0.4.
- A real notebook failing to list the USB may be BIOS/USB hardware compatibility, not necessarily a missing Legacy stage.

## Safe next build action for an approved operator

Run only inside the existing Fedora StorOS-BuildLab VM:

    cd ~/StorOS
    bash installer/build-ui-v05.sh

The build checks VM/Fedora, runs tests, verifies SSH-disabled base and produces a RAW at ~/StorOS/output/ui-v05/StorOS-v0.5-USB-Preview.raw without overwriting an existing output. It does not write physical drives.

After building, transfer the RAW to AEROCOOL as a sparse IMG, check SHA-256/size/GPT, and test the same IMG in SeaBIOS and OVMF with 2-4 GiB RAM. Confirm GUI and local API, masked SSH, and network restrictions. Only then distribute the IMG for balenaEtcher and a physical notebook test.

## Limits

Array/parity, writable pools, SMB/NFS administration, native authentication/RBAC, one-click Docker install and VM management are still incomplete. The v0.5 version number is a development preview label, not a production release. Its new image still needs both tests after building; the v0.4 result does not automatically certify v0.5.

## Lab cleanup and resource use

- After the Legacy GUI confirmation, both disposable BIOS QCOW2 overlays were removed (approximately 100 MiB allocated).
- Original v0.4 RAW IMG and all registered VM disks were preserved.
- BuildLab was shut down normally after the 61-test initial build-source check.
- A further 64 tests in the source tree pass with the v0.5 release-status tests added.
- No version 0.5 image artifact is present in AEROCOOL output; no claim of completing the blocked build.
