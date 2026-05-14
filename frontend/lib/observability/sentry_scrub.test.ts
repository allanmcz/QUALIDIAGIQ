import type { ErrorEvent, EventHint } from "@sentry/core";
import { describe, expect, it } from "vitest";

import { sentryBrowserBeforeSend } from "./sentry_scrub";

describe("sentryBrowserBeforeSend", () => {
  it("aceita evento mínimo sem request", () => {
    const event = { type: undefined } as ErrorEvent;
    expect(sentryBrowserBeforeSend(event, {})).toBe(event);
  });

  it("redacta request.data, user e extra sensíveis", () => {
    const event = {
      type: undefined,
      request: { data: { email: "a@b.com", password: "z", nome: "OK" } },
      user: { email: "t@t.com", username: "u", id: "99" },
      extra: { token_hint: "abc", ok: 1 },
    } as ErrorEvent;
    sentryBrowserBeforeSend(event, {} as EventHint);

    const req = event.request as { data: Record<string, unknown> };
    expect(req.data.email).toBe("[REDACTED]");
    expect(req.data.password).toBe("[REDACTED]");
    expect(req.data.nome).toBe("OK");
    const user = event.user as Record<string, unknown>;
    expect(user.email).toBe("[REDACTED]");
    expect(user.username).toBe("[REDACTED]");
    expect(user.id).toBe("99");
    const extra = event.extra as Record<string, unknown>;
    expect(extra.token_hint).toBe("[REDACTED]");
    expect(extra.ok).toBe(1);
  });

  it("redacta telefone e campo com codigo (OTP) em request.data", () => {
    const event = {
      type: undefined,
      request: {
        data: {
          telefone: "+5511999990000",
          codigo_verificacao: "987654",
          observacao: "sem dado sensivel",
        },
      },
    } as ErrorEvent;
    sentryBrowserBeforeSend(event, {} as EventHint);
    const data = (event.request as { data: Record<string, unknown> }).data;
    expect(data.telefone).toBe("[REDACTED]");
    expect(data.codigo_verificacao).toBe("[REDACTED]");
    expect(data.observacao).toBe("sem dado sensivel");
  });
});
