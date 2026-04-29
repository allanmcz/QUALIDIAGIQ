import { ShieldCheck } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex gap-2 items-center font-bold text-xl tracking-tight">
          <div className="w-8 h-8 rounded-md bg-primary text-primary-foreground flex items-center justify-center">
            Q
          </div>
          <span>QualiDiagIQ</span>
          <span className="text-muted-foreground font-normal text-sm ml-2 hidden sm:inline-block">
            by Tributiq
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <ShieldCheck className="w-4 h-4 text-accent" />
          <span className="hidden sm:inline-block">Conformidade ABNT NBR 17301</span>
        </div>
      </div>
    </header>
  );
}
