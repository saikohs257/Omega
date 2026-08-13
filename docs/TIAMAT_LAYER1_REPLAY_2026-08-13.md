# TIAMAT Layer-1 historical replay checkpoint

Source artifact:
- `layer1_structured_hazard_arm_pack_2020_2024.zip`
- SHA-256: `a8012c19c861fc55681adea9d6e5519297b953b321b31271189e3104f5371cdd`

Historical spine:
- 43,848 hourly rows
- 2020-01-01 00:00 through 2024-12-31 23:00
- 15 columns

Recovered replay against the exact supplied values:

| Check | Result |
|---|---:|
| Rows | 43,848 |
| Recovered active rows | 4,026 |
| Recovered starts | 453 |
| Entry-path mismatches | 0 |
| Entry-path agreement | 100.000% |
| Episode-type mismatches | 767 |
| Episode-type agreement | 98.251% |
| Age rows compared | 4,026 |
| Age mismatches | 0 |
| Age agreement | 100.000% |

Historical episode counts:
- none: 39,822
- trapped: 2,463
- mixed: 1,207
- phasic: 356

Recovered episode counts in the repository implementation:
- none: 39,822
- trapped: 2,699
- mixed: 862
- phasic: 465

Interpretation:

The recovered admission machine reproduces the historical active population and
453 episode starts exactly. The entry-path reconstruction is also exact, row for
row. Run age is exact on all 4,026 historical active rows.

The remaining 767 episode-type differences are a real archaeological target,
not a reason to relax the test. The current replay intentionally supplies an
empty daily `volratio` panel, so the recovered 3→4 gate falls back to its
historical neutral volume-expansion value. The historical tracker source has a
separate daily compression/volume chain; restoring that input is the next step
for closing the remaining episode-type gap.

This replay does not reconstruct the missing native LiveDeficit generator and
does not promote the historical module into the live Omega runtime.
