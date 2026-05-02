/**
 * Payload validado guardado no navegador (sessionStorage) até ao login.
 * Após JWT, o POST à API persiste o diagnóstico em PostgreSQL (Supabase), por tenant (RLS).
 */
export const STORAGE_PENDING_DIAGNOSTICO = "qdi_pending_post_diagnostico_v1";
