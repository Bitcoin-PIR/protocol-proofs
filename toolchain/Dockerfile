# EasyCrypt's release build environment fixes OCaml, Why3, and supported SMT
# solvers. The OCI digest prevents a moving tag from changing proof CI.
FROM ghcr.io/easycrypt/ec-build-box@sha256:5a46a4d816e763ad5de9ee9502d52158c742b9b98cc1f60c443d135a270fdb6a

ARG EASYCRYPT_COMMIT=dd9bd930d45e81980e546fc835ed2022418644be
ARG OCAML_VERSION=4.14.1
ARG WHY3_VERSION=1.8.2
ARG ALT_ERGO_VERSION=2.6.3
ARG PROOF_SWITCH=bitcoinpir-proof

# A single package-build job is deterministic across CI and avoids the
# Rosetta/futex deadlock seen when locally validating linux/amd64 on arm64.
ENV OPAMJOBS=1 \
    DUNEJOBS=1

LABEL org.opencontainers.image.source="https://github.com/Bitcoin-PIR/protocol-proofs" \
      org.opencontainers.image.description="Pinned EasyCrypt toolchain for BitcoinPIR protocol proofs" \
      org.bitcoinpir.easycrypt.commit="${EASYCRYPT_COMMIT}" \
      org.bitcoinpir.ocaml.version="${OCAML_VERSION}" \
      org.bitcoinpir.why3.version="${WHY3_VERSION}" \
      org.bitcoinpir.alt-ergo.version="${ALT_ERGO_VERSION}"

RUN opam switch create --no-switch "${PROOF_SWITCH}" \
      "ocaml-base-compiler.${OCAML_VERSION}"

RUN opam pin add --switch="${PROOF_SWITCH}" -n why3 "${WHY3_VERSION}" && \
    opam pin add --switch="${PROOF_SWITCH}" -n alt-ergo "${ALT_ERGO_VERSION}" && \
    opam pin add --switch="${PROOF_SWITCH}" -n easycrypt \
      "git+https://github.com/EasyCrypt/easycrypt.git#${EASYCRYPT_COMMIT}"

RUN opam install --switch="${PROOF_SWITCH}" --jobs=1 \
      --confirm-level=unsafe-yes alt-ergo easycrypt

RUN rm -f "$HOME/.why3.conf" "$HOME/.config/easycrypt/why3.conf" && \
    opam exec --switch="${PROOF_SWITCH}" -- easycrypt why3config

WORKDIR /proofs

ENTRYPOINT ["opam", "exec", "--switch=bitcoinpir-proof", "--"]
CMD ["make", "check"]
