-- Documentação operacional: idempotência global (sem RLS por tenant na linha).
-- Ver docs/operacao_rls_idempotency.md.

COMMENT ON TABLE idempotency_responses IS $c$
Cache POST /diagnosticos/ por hash(Idempotency-Key + Authorization). Sem tenant_id por linha; isolamento via hash (middleware).
$c$;

COMMENT ON COLUMN idempotency_responses.chave_hash IS $c$
SHA-256 hex de metodo + path + idempotency_key + authorization_header.
$c$;
