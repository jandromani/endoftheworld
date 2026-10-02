# Cross-platform release flasher

The flasher is the simple path for a user who receives a prebuilt signed Ark
release and does **not** want to run the Linux image-builder.

Supported code paths:

- Windows: physical disks via PowerShell/Get-Disk.
- macOS: external physical disks via diskutil.
- Linux: whole block devices via lsblk/findmnt.

## Trust model

Before showing a release as verified, the flasher checks:

1. the release public-key fingerprint embedded in the signed manifest;
2. the detached RSA/SHA-256 manifest signature;
3. SHA-256 + byte size of every bound release file;
4. the signed raw-image byte count and SHA-256 while decompression/flashing occurs.

For a compressed release, the \`.img.zst\` is streamed directly to the target.
A second uncompressed 58 GB temporary image is not required.

## Run from source

\`\`\`bash
python -m pip install -r flasher/requirements.txt
python flasher/ark_flasher.py
\`\`\`

Launching with no subcommand opens the Tk desktop UI.

CLI examples:

\`\`\`bash
python flasher/ark_flasher.py verify ./nano-release
python flasher/ark_flasher.py list
python flasher/ark_flasher.py flash ./nano-release /dev/sdX --confirm "ERASE /dev/sdX"
\`\`\`

On Windows the target form is similar to:

\`\\\\.\\PhysicalDrive2\`

and requires Administrator privileges.

## Safety rules

The flasher:

- requires the target to be a currently enumerated physical disk;
- rejects the running/system disk;
- rejects mounted Linux targets;
- rejects targets smaller than the signed raw image;
- requires the literal \`ERASE <device>\` confirmation;
- verifies the decompressed raw image hash while writing.

macOS targets are unmounted with \`diskutil\` immediately before write. Windows
targets are temporarily taken offline before write and brought back online
afterwards.

## Packaged binaries

The repository has two workflows:

- \`flasher-validate.yml\`: self-tests source + packaged executable on Linux,
  Windows and macOS for every relevant PR.
- \`flasher-package.yml\`: creates downloadable one-file executables manually or
  from a \`flasher-v*\` tag.

These tests prove packaging and byte-stream correctness. They do not replace a
real destructive-flash test on physical media.
