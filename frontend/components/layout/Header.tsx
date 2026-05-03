import Link from "next/link";
import { ShieldCheck } from "lucide-react";

import { Logo } from "@/components/brand/Logo";
import { HeaderAuthNav } from "@/components/layout/HeaderAuthNav";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between gap-3">
        <Link
          href="/"
          className="flex min-h-[44px] min-w-0 shrink-0 items-center py-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-md"
        >
          <Logo variant="full" size="xl" priority />
        </Link>
        <div className="flex min-w-0 items-center gap-2 sm:gap-3">
          <div
            className="hidden min-w-0 items-center gap-2 text-sm text-muted-foreground sm:flex"
            title="Conformidade ABNT NBR 17301"
          >
            <ShieldCheck className="h-5 w-5 shrink-0 text-accent" aria-hidden />
            <span className="hidden truncate lg:inline">Conformidade ABNT NBR 17301</span>
          </div>
          <HeaderAuthNav />
        </div>
      </div>
    </header>
  );
}
