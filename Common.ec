(* ---------------------------------------------------------------------- *
 * Common.ec — shared abstract types for the BitcoinPIR leakage proof.
 *
 * Treat the cryptographic primitives (DPF, FHE, PRP) as black boxes:
 * we model their wire output as freshly-sampled uniform randomness over
 * a domain of fixed length, parameterised by the security parameter.
 * The theorems in `Theorem.ec` are conditional on the standard ideal
 * functionalities (PRP indistinguishability, DPF privacy, FHE IND-CPA);
 * those reductions live in the primitives' respective papers.
 * --------------------------------------------------------------------- *)

require import AllCore List Distr Int.

(* ---------- Protocol parameters ---------- *
 * Concrete values for the public deployment (cf. CLAUDE.md):
 *   K              = 75   — INDEX-level groups per round
 *   K_CHUNK        = 80   — CHUNK-level groups per round
 *   INDEX_CUCKOO   = 2    — cuckoo positions per INDEX query
 * Modelled as `op` constants so any reasoning that depends on the
 * specific values can refer to them; existing tests hard-code the
 * same numbers.
 *)
op K : int = 75.
op K_chunk : int = 80.
op index_cuckoo_num_hashes : int = 2.

axiom K_pos        : 1 <= K.
axiom K_chunk_pos  : 1 <= K_chunk.
axiom index_cuckoo : 2 <= index_cuckoo_num_hashes.

(* ---------- Query domain ---------- *
 * A `query` abstracts a 20-byte HASH160 scripthash plus a database id.
 * The transcript proof never inspects the bytes — privacy reduces to
 * "the wire shape is independent of the bytes" — so we leave it as
 * an abstract type.
 *
 * `db_id` is exposed via the accessor `query_db_id` because every PIR
 * round's `round_profile` carries `db_id_opt = Some (query_db_id q)`.
 * The simulator must read this from the leakage record (where it is
 * admitted as `query_db_id`) — not from `q` — to build the same
 * transcript. The accessor lets the `Real` module read it directly
 * from the query while `Sim` reads the corresponding leakage axis.
 *)
type query.
type db_id.

(* Payment V1 authorization is provider-local.  The functions below are
 * indexed by the logical server id so the model never assumes that two PIR
 * providers chose the same method, scope, operation, timing, or result shape. *)
type authorization_scheme.
type service_scope_id.
type authorization_operation.
type authorization_timing.
type authorization_result_shape.

op query_db_id : query -> db_id.
op query_authorization_scheme : query -> int -> authorization_scheme.
op query_authorization_scope_id : query -> int -> service_scope_id.
op query_authorization_operation : query -> int -> authorization_operation.
op query_authorization_timing : query -> int -> authorization_timing.
op query_authorization_result_shape : query -> int -> authorization_result_shape.

(* ---------- Wire transcript ---------- *
 * The server-observable transcript is a list of per-round events.
 * Each event captures exactly the wire-observable shape:
 *   - which round-kind  (categorical)
 *   - which server      (0 = primary, 1 = secondary; OnionPIR is
 *                        single-server so always 0)
 *   - request_bytes / response_bytes — wire payload sizes including
 *     the 4-byte length prefix
 *   - items — the per-round per-group / per-query item count (length
 *     and value semantics depend on `kind`; see RoundProfile in
 *     the `pir_sdk::leakage` implementation surface named by the wire
 *     contract for the full mapping).
 *
 * Concrete byte-level content is not modelled — by hypothesis the
 * cryptographic primitives produce uniformly random bytes inside fixed-
 * length envelopes, so transcript-distinguishability reduces to the
 * shape data here.
 *)
type round_kind = [
  | RIndex
  | RChunk
  | RIndexMerkleSiblings of int  (* level *)
  | RChunkMerkleSiblings of int  (* level *)
  | RHarmonyHintRefresh
  | ROnionKeyRegister
  | RInfo
  | RServiceAuthorization
  | RMerkleTreeTops
].

type round_profile = {
  kind           : round_kind;
  server_id      : int;
  db_id_opt      : db_id option;
  request_bytes  : int;
  response_bytes : int;
  items          : int list;
  authorization_scheme_opt      : authorization_scheme option;
  authorization_scope_id_opt    : service_scope_id option;
  authorization_operation_opt   : authorization_operation option;
  authorization_timing_opt      : authorization_timing option;
  authorization_result_shape_opt : authorization_result_shape option;
}.

type transcript = round_profile list.

(* Sanity: the empty transcript (no rounds emitted) is well-defined.
 * Real protocol runs always emit at least the catalog Info round. *)
op empty_transcript : transcript = [].

(* ---------- Backend tag ---------- *
 * Modelled abstractly because the simulator argument is per-backend
 * but the L definition is shared across all three.
 *)
type backend = [ BDpf | BHarmony | BOnion ].
