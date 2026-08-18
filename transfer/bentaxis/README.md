# BentAxis Binary Transfer v1

Staging branch for the canonical BentAxis bundle.

This branch is intentionally isolated from `main` until binary reconstruction and SHA-256 verification pass.

Source artifact: `BentTesseract_COMPLETE_CURRENT_WITH_BU4_20260614.tar.xz`

Transfer protocol:
1. Base64 chunks are staged under this directory.
2. A manually dispatched GitHub Actions workflow reconstructs the binary.
3. The runner verifies the reconstructed SHA-256 against the source manifest.
4. Only a byte-exact reconstruction may be committed to the final artifact path.
