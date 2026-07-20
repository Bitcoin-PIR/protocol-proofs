# Verification entry points for the BitcoinPIR EasyCrypt proof suite.

PYTHON             ?= python3
EASYCRYPT          ?= easycrypt compile
EC_OPTS            ?= -I .
DOCKER              ?= docker
TOOLCHAIN_IMAGE     ?= bitcoinpir/protocol-proofs-toolchain:local
CONTAINER_PLATFORM  ?= linux/amd64

.PHONY: all check manifest-check proof-check verbose container-build container-check record clean

all: check

check: manifest-check proof-check

manifest-check:
	$(PYTHON) scripts/verify_manifest.py

proof-check:
	$(EASYCRYPT) $(EC_OPTS) Theorem.ec

verbose: manifest-check
	$(EASYCRYPT) $(EC_OPTS) -p alt-ergo -p z3 Theorem.ec

container-build:
	$(DOCKER) build \
		--platform $(CONTAINER_PLATFORM) \
		-f toolchain/Dockerfile \
		-t $(TOOLCHAIN_IMAGE) \
		.

container-check: container-build
	$(DOCKER) run --rm \
		--platform $(CONTAINER_PLATFORM) \
		-v "$(CURDIR):/proofs" \
		-w /proofs \
		$(TOOLCHAIN_IMAGE) \
		make check

record: check
	$(PYTHON) scripts/write_verification_record.py --output verification-record.json

clean:
	rm -f *.ecpc *.eco *.ecaut verification-record.json
