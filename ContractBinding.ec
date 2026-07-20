(* @generated from BitcoinPIR/wire-shape-contract/v1; do not edit. *)
(* contract-sha256: 1b0df1150e885abe0446afe5b960a471c67e458905ab54f9aa8799c42bc2c673 *)

require import Common Leakage Protocol Protocol_DPF Protocol_Harmony Protocol_Onion.
require import AllCore List Int.

op contract_round_kinds : round_kind list =
  [RIndex; RChunk; RIndexMerkleSiblings 0; RChunkMerkleSiblings 0; RHarmonyHintRefresh; ROnionKeyRegister; RInfo; RMerkleTreeTops].

op contract_leakage (q : query) : leakage =
  {| index_max_items_per_group_per_level = query_index_max q;
     chunk_max_items_per_group_per_level = query_chunk_max q;
     session_query_index                 = query_session_query_index q;
     query_db_id                         = query_db_id q; |}.

lemma contract_index_groups : K = 75.
proof. by trivial. qed.

lemma contract_chunk_groups : K_chunk = 80.
proof. by trivial. qed.

lemma contract_index_cuckoo_hashes : index_cuckoo_num_hashes = 2.
proof. by trivial. qed.

lemma contract_dpf_server_ids : pir_server_ids BDpf = [0; 1].
proof. exact pir_server_ids_dpf. qed.

lemma contract_harmony_server_ids : pir_server_ids BHarmony = [0].
proof. exact pir_server_ids_harmony. qed.

lemma contract_onion_server_ids : pir_server_ids BOnion = [0].
proof. exact pir_server_ids_onion. qed.

lemma contract_round_kind_count : size contract_round_kinds = 8.
proof. by trivial. qed.

lemma contract_leakage_matches (q : query) : L q = contract_leakage q.
proof. by rewrite /contract_leakage L_factors. qed.
