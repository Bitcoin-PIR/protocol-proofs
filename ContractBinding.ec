(* @generated from BitcoinPIR/wire-shape-contract/v1; do not edit. *)
(* contract-sha256: 648227ffba4946b5adc55291bdb77eb452d93a5c03c553a17dc6f5d053b97bf7 *)

require import Common Leakage Protocol Protocol_DPF Protocol_Harmony Protocol_Onion.
require import AllCore List Int.

op contract_round_kinds : round_kind list =
  [RIndex; RChunk; RIndexMerkleSiblings 0; RChunkMerkleSiblings 0; RHarmonyHintRefresh; ROnionKeyRegister; RInfo; RServiceAuthorization; RMerkleTreeTops].

op contract_leakage (q : query) : leakage =
  {| index_max_items_per_group_per_level = query_index_max q;
     chunk_max_items_per_group_per_level = query_chunk_max q;
     session_query_index                 = query_session_query_index q;
     query_db_id                         = query_db_id q;
     authorization_scheme_by_server      = query_authorization_scheme q;
     authorization_scope_id_by_server    = query_authorization_scope_id q;
     authorization_operation_by_server   = query_authorization_operation q;
     authorization_timing_by_server      = query_authorization_timing q;
     authorization_result_shape_by_server = query_authorization_result_shape q; |}.

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

lemma contract_round_kind_count : size contract_round_kinds = 9.
proof. by trivial. qed.

lemma contract_service_auth_request_opcode : service_auth_request_opcode = 14.
proof. by trivial. qed.

lemma contract_service_auth_response_opcode : service_auth_response_opcode = 14.
proof. by trivial. qed.

lemma contract_service_auth_padding_class : service_auth_padding_class_wire_id = 1.
proof. by trivial. qed.

lemma contract_service_auth_body_bytes : service_auth_body_bytes = 16384.
proof. by trivial. qed.

lemma contract_service_auth_canonical_padding : service_auth_canonical_padding_byte = 0.
proof. by trivial. qed.

lemma contract_service_auth_inner_plaintext_bytes : service_auth_inner_plaintext_bytes = 16385.
proof. by trivial. qed.

lemma contract_service_auth_sealed_payload_bytes : service_auth_sealed_payload_bytes = 16410.
proof. by trivial. qed.

lemma contract_service_auth_application_record_bytes : service_auth_application_record_bytes = 16414.
proof. by trivial. qed.

lemma contract_service_auth_requires_secure_channel : service_auth_secure_channel_required = true.
proof. by trivial. qed.

lemma contract_service_auth_response_is_variable : service_auth_response_fixed_length = false.
proof. by trivial. qed.

lemma contract_service_auth_result_shape_is_observable :
  service_auth_result_shape_observable_from_ciphertext_length = true.
proof. by trivial. qed.

lemma contract_leakage_matches (q : query) : L q = contract_leakage q.
proof. by rewrite /contract_leakage L_factors. qed.
