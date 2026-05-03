import { redirect } from "next/navigation";

/** Entrada `/dashboard` — lista e ações ficam em `/dashboard/diagnosticos`. */
export default function DashboardIndexPage() {
  redirect("/dashboard/diagnosticos");
}
