# BentAxis / Tesseract archive deposit manifest

Imported and audited locally on 2026-08-18 from the six uploaded 2026-06-14 archives.

| Archive | Bytes | SHA-256 | Extracted files | Source-ish files |
|---|---:|---|---:|---:|
| `BentTesseract_COMPLETE_CURRENT_WITH_BU4_20260614.tar.xz` | 6,076,144 | `9a4608fc527e9f3d9b3447c2b79e736732e36ae9b60d68a97b42501e420dfd0e` | 1,106 | 511 |
| `BentAxis_B40_6_HYPERCELL_ACCELERATOR_IMPL_20260614.tar.xz` | 1,351,056 | `7e25eaec4ff32d0dc1ff8acf8d1eb76e96f70179cd29e89dd7d9fbff7b211440` | 1,037 | 468 |
| `BentAxis_B39_ContractBackedEncoder_Pack_20260614.tar.xz` | 977,868 | `3056f907110ba882dc6b73d44ec71227b28a5ae4dd80b92adc8810ee7a2d1291` | 932 | 422 |
| `BentAxis_BU2_HotWarmColdSpeedCourts_Pack_20260614.tar.xz` | 25,376 | `5c43def2f0ffb9794a48f758023c66c3e8475bec9c175907b95f8d24284a198b` | 41 | 23 |
| `BentTesseract_FIX_HANDOFF_BU4_20260614.tar.zst` | 7,898 | `407c4490a5ac04e0ea2424ede1b602c104d519c91b5cd752bfe7a0d48d46626e` | 6 | 4 |
| `BENTUPGRADE_TESSERACT_PROFILE_V1_20260614.tar.zst` | 8,986 | `8112f50d48cc8042219ba52e3b32b1c1f3f821d98a00696923eabbd79a1ea2ff` | 6 | 3 |

## Audit result

The complete bundle contains BU1/BU2/BU3/BU4 source/report packs plus B39 and B40.6 lineage. The extracted complete bundle contains 151 implementation files under the retained BU3 TesseractHotIndexStore tree, while the full six-archive set contains 3,128 extracted files.

The B40.6 bundle contains `hypercell_accelerator_index_1.py` and the associated BAX/Tesseract implementation lineage. The BU2 pack contains the explicit HOT/WARM/COLD routing, codecs, temperature classifier, speed ledger, and contracts. The B39 pack contains the contract-backed encoder and earlier axis/court lineage.

## Repository handling

The GitHub connector available in this session can create text blobs/files but cannot transfer the uploaded local binary archives directly into GitHub as binary objects. Therefore this commit records the verified archive inventory and hashes rather than pretending that a truncated text/base64 conversion is a valid binary deposit.

The original six archives remain available in the conversation workspace and are the byte-exact source artifacts for the next binary-capable repository transfer.
