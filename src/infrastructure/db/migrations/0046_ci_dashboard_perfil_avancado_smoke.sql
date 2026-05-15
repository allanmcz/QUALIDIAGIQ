-- Admin CI Playwright com perfil avançado — smoke live explicacao-score-llm (POST não retorna 403).
-- Senha documentada: secret (ver 0005a_ci_playwright_admin.sql).

UPDATE admins
SET perfil_conta = 'avancado'
WHERE lower(trim(email)) = lower(trim('ci-dashboard@qualidiagiq.test'));
