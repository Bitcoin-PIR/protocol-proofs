# BitcoinPIR protocol proofs

This repository contains the EasyCrypt model and mechanically checked
simulator-property proof for the wire shape of BitcoinPIR queries.

The proof sources retain their history from
[`Bitcoin-PIR/Bitcoin-PIR`](https://github.com/Bitcoin-PIR/Bitcoin-PIR), where
they originally lived under `proofs/easycrypt/`.

## Status

`make check` checks the machine-readable manifest and compiles `Theorem.ec`.
At the extracted source snapshot, all 39 declared lemmas close and the proof
scripts contain no `admit`, `sorry`, or `abort` command.

That statement is intentionally narrower than “BitcoinPIR is proven private.”
This repository proves properties of an abstract wire-shape model under the
assumptions listed in [`proof-manifest.json`](proof-manifest.json). It does not
mechanically establish that every Rust, TypeScript, WASM, server, or deployed
binary implements that model.

## Mechanically checked claims

The top-level proof establishes:

- per-query factorization: two queries with equal leakage records produce the
  same modeled transcript;
- a constructive simulator that produces the same modeled transcript using
  only the leakage record;
- the corresponding multi-query statements for sequences of equal length;
- backend-specific round-count facts for DPF, HarmonyPIR, and OnionPIR.

The transcript records round kind, server id, database id, request/response
byte counts, and per-round item counts. Because payload bytes are not modeled,
the proof is a deterministic equality proof. Interpreting it as a
computational privacy statement additionally relies on the ideal-primitive
assumptions for DPF, FHE, and PRP.

The admitted leakage record contains:

- INDEX Merkle maximum items per group and level;
- CHUNK Merkle maximum items per group and level;
- session query position, including HarmonyPIR hint-refresh timing;
- database id.

## Explicit non-claims

This proof does not establish:

- security of DPF, FHE, PRP, hash functions, or their concrete
  implementations;
- secrecy of payload contents outside the ideal-primitive hypothesis;
- timing, CPU, packet-arrival, connection, TLS, WebSocket, IP, or compression
  side-channel resistance;
- behavior of OnionPIR retry paths after server-controlled LRU eviction;
- correctness, memory safety, attestation, database-root validity, Merkle
  inclusion, or result correctness;
- mechanical correspondence between the EasyCrypt model and production code.

The authoritative machine-readable claim, assumption, and non-claim list is
[`proof-manifest.json`](proof-manifest.json). Human-readable source commentary
in [`Leakage.ec`](Leakage.ec) provides additional rationale.

The manifest also inventories every EasyCrypt `axiom` by name, source file,
and normalized statement SHA-256. CI rejects a new axiom, a renamed axiom, or a
changed axiom statement until the manifest and consumer lock are explicitly
reviewed and updated.

The reviewed source closure consists only of the root-level `.ec` files listed
in the manifest. CI rejects abstract-theory `.eca` files, `easycrypt.project`,
and precompiled EasyCrypt artifacts so the fixed compile command cannot load
an unmanifested proof input.

## Relationship to the implementation

The manifest records the source repository and the last commit that changed
this proof snapshot. It is bound to the raw SHA-256 of a
`BitcoinPIR/wire-shape-contract/v1` contract generated in the product
repository. Source history and a contract digest provide provenance and drift
detection; they are not by themselves an implementation refinement proof.

The intended integration is for the product repository to generate a small,
machine-readable wire-contract document and lock both:

1. the exact `protocol-proofs` commit that passes CI; and
2. the digest of the matching wire contract.

The product repository must still lock the exact proof commit, manifest digest,
contract digest, and passing verification record. A green check here alone
means only that this proof suite passed for this repository commit.

The product repository independently regenerates `ContractBinding.ec` from its
wire contract, compares the exact bytes, validates the complete source/import
set, and compiles `Theorem.ec` using its own digest-locked verifier. The proof
repository's Makefile, Dockerfile, and verification record are not treated as
the production trust root.

## Repository layout

| Path | Role |
|---|---|
| `Common.ec` | Shared abstract types and public protocol parameters |
| `ContractBinding.ec` | Generated, compiled binding to the product wire contract |
| `Leakage.ec` | Leakage function, admitted axes, and explicit non-claims |
| `Protocol.ec` | Abstract real wire-shape model |
| `Simulator.ec` | Simulator using only the leakage record |
| `Protocol_DPF.ec` | DPF backend specialization |
| `Protocol_Harmony.ec` | HarmonyPIR backend specialization |
| `Protocol_Onion.ec` | OnionPIR backend specialization |
| `Theorem.ec` | Per-query and multi-query simulator theorems |
| `proof-manifest.json` | Machine-readable claims, assumptions, toolchain, and source hashes |
| `toolchain/Dockerfile` | Reproducible EasyCrypt verification environment |
| `scripts/verify_manifest.py` | Manifest, source-hash, theorem, and proof-hole checks |

## Reproduce the check

### Pinned container (recommended)

Docker is the only host dependency:

```bash
make container-check
```

The Dockerfile pins the EasyCrypt build image by OCI digest and installs
EasyCrypt from an exact Git commit. The same path runs in GitHub Actions.

### Existing local EasyCrypt installation

If EasyCrypt is already installed:

```bash
make check
```

The canonical container and the original native verification baseline both
use EasyCrypt commit `dd9bd930d45e81980e546fc835ed2022418644be`, OCaml
4.14.1, Why3 1.8.2, and Alt-Ergo 2.6.3.

## CI evidence

Every push, pull request, and merge queue run executes the manifest checks and
`easycrypt compile -I . Theorem.ec` inside the pinned toolchain. A successful
job uploads `verification-record.json`, which binds the result to:

- repository commit and GitHub Actions run;
- proof manifest digest;
- aggregate proof-source digest;
- pinned container base and EasyCrypt commit;
- exact verification command.

The record is generated only after the check succeeds. It records exit code `0`
and states the derivation from that exit code to `result: passed`. It is evidence
from the corresponding GitHub Actions run, not a self-authenticating statement
merely because its JSON field says `passed`.

## Updating the proof

After changing any `.ec` file:

1. update the affected claims or assumptions in `proof-manifest.json`;
2. refresh each changed `sources[].sha256` value;
3. run `make check` or `make container-check`;
4. update the product repository’s proof/contract lock when the change affects
   the implementation contract.

The manifest checker rejects undeclared EasyCrypt files, stale hashes, missing
claim theorems, changed lemma counts, and proof-hole commands outside comments.

## License

Licensed under either Apache License 2.0 or the MIT license, at your option.
See [`LICENSE-APACHE`](LICENSE-APACHE) and [`LICENSE-MIT`](LICENSE-MIT).
