#!/usr/bin/env python3
"""Fail closed when proof sources and their declared claims drift apart."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "proof-manifest.json"
REQUIRED_CONSUMER_LOCK_FIELDS = [
    "protocolProofs.commit",
    "protocolProofs.manifestSha256",
    "implementationContract.sha256",
    "protocolProofs.verificationRecordSha256",
]
COMPILED_PROOF_SUFFIXES = {".eco", ".ecpc", ".ecaut"}
FORBIDDEN_PROOF_FILENAMES = {"easycrypt.project"}
FORBIDDEN_PROOF_SUFFIXES = {".eca"}


def fail(message: str) -> None:
    print(f"manifest check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strip_easycrypt_comments(text: str) -> str:
    """Remove nested EasyCrypt/OCaml comments without changing tokens."""
    result: list[str] = []
    depth = 0
    index = 0
    while index < len(text):
        pair = text[index : index + 2]
        if pair == "(*":
            depth += 1
            index += 2
            continue
        if pair == "*)":
            if depth == 0:
                fail("encountered an unmatched comment terminator")
            depth -= 1
            index += 2
            continue
        if depth == 0:
            result.append(text[index])
        index += 1
    if depth != 0:
        fail("encountered an unterminated EasyCrypt comment")
    return "".join(result)


def require_type(value: object, expected: type, field: str) -> None:
    if not isinstance(value, expected):
        fail(f"{field} must be {expected.__name__}")


def main() -> None:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"cannot load proof-manifest.json: {error}")

    require_type(manifest, dict, "manifest")
    if manifest.get("schema_version") != 1:
        fail("schema_version must be 1")
    if manifest.get("proof_suite") != "bitcoinpir-wire-shape-simulator":
        fail("unexpected proof_suite")

    expected_lemma_count = manifest.get("expected_lemma_count")
    if not isinstance(expected_lemma_count, int) or expected_lemma_count <= 0:
        fail("expected_lemma_count must be a positive integer")

    sources = manifest.get("sources")
    require_type(sources, list, "sources")
    declared_paths: set[str] = set()
    code_parts: list[str] = []
    source_code: dict[str, str] = {}

    for index, source in enumerate(sources):
        require_type(source, dict, f"sources[{index}]")
        relative = source.get("path")
        expected_hash = source.get("sha256")
        if not isinstance(relative, str) or not relative.endswith(".ec"):
            fail(f"sources[{index}].path must name a root-level .ec file")
        path = Path(relative)
        if path.is_absolute() or len(path.parts) != 1 or ".." in path.parts:
            fail(f"unsafe or non-root source path: {relative}")
        if relative in declared_paths:
            fail(f"duplicate source declaration: {relative}")
        declared_paths.add(relative)

        full_path = ROOT / path
        if not full_path.is_file() or full_path.is_symlink():
            fail(f"source is missing, not a regular file, or a symlink: {relative}")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            fail(f"invalid sha256 for {relative}")
        actual_hash = sha256(full_path)
        if actual_hash != expected_hash:
            fail(
                f"stale hash for {relative}: expected {expected_hash}, got {actual_hash}"
            )
        stripped = strip_easycrypt_comments(full_path.read_text(encoding="utf-8"))
        code_parts.append(stripped)
        source_code[relative] = stripped

    actual_paths: set[str] = set()
    for full_path in ROOT.rglob("*.ec"):
        relative = full_path.relative_to(ROOT)
        if ".git" in relative.parts:
            continue
        if not full_path.is_file() or full_path.is_symlink():
            fail(f"proof tree contains a non-regular .ec entry: {relative}")
        actual_paths.add(relative.as_posix())
    if actual_paths != declared_paths:
        missing = sorted(actual_paths - declared_paths)
        stale = sorted(declared_paths - actual_paths)
        fail(f"source set drifted; undeclared={missing}, missing={stale}")

    forbidden_inputs: list[str] = []
    for full_path in ROOT.rglob("*"):
        relative = full_path.relative_to(ROOT)
        if ".git" in relative.parts:
            continue
        if (
            full_path.name in FORBIDDEN_PROOF_FILENAMES
            or full_path.suffix.lower() in FORBIDDEN_PROOF_SUFFIXES
        ):
            forbidden_inputs.append(relative.as_posix())
    if forbidden_inputs:
        fail(f"proof tree contains unreviewed EasyCrypt inputs: {sorted(forbidden_inputs)}")

    tracked_result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=False,
        capture_output=True,
    )
    if tracked_result.returncode != 0:
        fail(
            "cannot list tracked proof files: "
            f"{tracked_result.stderr.decode(errors='replace').strip()}"
        )
    tracked_files = {
        entry.decode("utf-8")
        for entry in tracked_result.stdout.split(b"\0")
        if entry
    }
    tracked_sources = {
        path for path in tracked_files if Path(path).suffix.lower() == ".ec"
    }
    if tracked_sources != declared_paths:
        fail(
            "tracked EasyCrypt source set differs from the manifest; "
            f"extra={sorted(tracked_sources - declared_paths)}, "
            f"missing={sorted(declared_paths - tracked_sources)}"
        )
    tracked_forbidden = sorted(
        path
        for path in tracked_files
        if Path(path).name in FORBIDDEN_PROOF_FILENAMES
        or Path(path).suffix.lower()
        in FORBIDDEN_PROOF_SUFFIXES | COMPILED_PROOF_SUFFIXES
    )
    if tracked_forbidden:
        fail(f"proof commit contains unreviewed EasyCrypt inputs: {tracked_forbidden}")

    code = "\n".join(code_parts)
    proof_holes = sorted(set(re.findall(r"\b(?:admit|sorry|abort)\b", code)))
    if proof_holes:
        fail(f"proof-hole commands found outside comments: {proof_holes}")

    lemmas = re.findall(r"\blemma\s+([A-Za-z_][A-Za-z0-9_']*)", code)
    if len(lemmas) != expected_lemma_count:
        fail(f"expected {expected_lemma_count} lemmas, found {len(lemmas)}")
    if len(set(lemmas)) != len(lemmas):
        fail("duplicate lemma names found")

    extracted_axioms: list[dict[str, str]] = []
    for source_path, text in source_code.items():
        for match in re.finditer(
            r"\baxiom\s+([A-Za-z_][A-Za-z0-9_']*)\s*:(.*?\.)", text, re.DOTALL
        ):
            canonical = re.sub(r"\s+", " ", match.group(0)).strip()
            extracted_axioms.append(
                {
                    "name": match.group(1),
                    "source": source_path,
                    "statement_sha256": hashlib.sha256(
                        canonical.encode("utf-8")
                    ).hexdigest(),
                }
            )
    extracted_axioms.sort(key=lambda item: (item["source"], item["name"]))
    if manifest.get("axioms") != extracted_axioms:
        fail("axiom inventory or normalized statement digest drifted")

    claims = manifest.get("claims")
    require_type(claims, list, "claims")
    if not claims:
        fail("at least one claim is required")
    claim_ids: set[str] = set()
    for index, claim in enumerate(claims):
        require_type(claim, dict, f"claims[{index}]")
        claim_id = claim.get("id")
        theorem = claim.get("theorem")
        if not isinstance(claim_id, str) or not claim_id:
            fail(f"claims[{index}].id is required")
        if claim_id in claim_ids:
            fail(f"duplicate claim id: {claim_id}")
        claim_ids.add(claim_id)
        if theorem not in lemmas:
            fail(f"claim {claim_id} references missing theorem {theorem!r}")
        assumption_ids = claim.get("depends_on_assumptions")
        require_type(assumption_ids, list, f"claims[{index}].depends_on_assumptions")

    assumptions = manifest.get("assumptions")
    require_type(assumptions, list, "assumptions")
    known_assumptions = {
        assumption.get("id")
        for assumption in assumptions
        if isinstance(assumption, dict) and isinstance(assumption.get("id"), str)
    }
    if len(known_assumptions) != len(assumptions):
        fail("assumption ids must be present and unique")
    for claim in claims:
        unknown = set(claim["depends_on_assumptions"]) - known_assumptions
        if unknown:
            fail(f"claim {claim['id']} references unknown assumptions: {sorted(unknown)}")

    non_claims = manifest.get("explicit_non_claims")
    require_type(non_claims, list, "explicit_non_claims")
    if not non_claims:
        fail("explicit_non_claims must not be empty")

    binding = manifest.get("implementation_binding")
    require_type(binding, dict, "implementation_binding")
    if binding.get("status") not in {"not-mechanized", "contract-hash-bound"}:
        fail("implementation_binding.status is not recognized")
    if binding.get("status") == "contract-hash-bound":
        if binding.get("contract_schema") != "BitcoinPIR/wire-shape-contract/v1":
            fail("contract-hash-bound manifest requires the v1 BitcoinPIR wire contract schema")
        contract_hash = binding.get("wire_contract_sha256")
        if not isinstance(contract_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", contract_hash):
            fail("contract-hash-bound manifests require wire_contract_sha256")
        if binding.get("generated_source") != "ContractBinding.ec":
            fail("contract-hash-bound manifests require ContractBinding.ec")
        if binding.get("required_consumer_lock_fields") != REQUIRED_CONSUMER_LOCK_FIELDS:
            fail("required_consumer_lock_fields does not match the v1 consumer lock schema")

    print(
        f"manifest check passed: {len(sources)} sources, "
        f"{len(lemmas)} lemmas, {len(claims)} claims"
    )


if __name__ == "__main__":
    main()
