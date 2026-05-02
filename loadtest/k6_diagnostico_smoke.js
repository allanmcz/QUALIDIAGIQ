/**
 * Smoke HTTP para diagnóstico de carga leve (k6).
 *
 * Uso:
 *   BASE_URL=http://127.0.0.1:8000 k6 run loadtest/k6_diagnostico_smoke.js
 */
import http from "k6/http";
import { check } from "k6";

export const options = {
  vus: 1,
  duration: "30s",
  thresholds: {
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const base = __ENV.BASE_URL || "http://127.0.0.1:8000";
  const res = http.get(`${base.replace(/\/$/, "")}/health`);
  check(res, {
    "health 200": (r) => r.status === 200,
  });
}
