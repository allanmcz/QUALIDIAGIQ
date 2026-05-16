-- INSERTs legados (testes integração, scripts) omitindo a coluna: default alinhado ao domínio.
ALTER TABLE diagnosticos
    ALTER COLUMN painel_estado_ciclo SET DEFAULT 'em_andamento';
