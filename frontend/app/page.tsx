"use client";

import { useEffect, useMemo, useState } from "react";

/* ───────── types ───────── */
type Mode = "tabular" | "relational" | "documents";
type Row = Record<string, string | number | null>;
type Tables = Record<string, Row[]>;
type DocKind = "invoice" | "statement";
type Cfg = { rows: number; seed: number; noise: number; masking: boolean; hashing: boolean };
type Invoice = { kind: "invoice"; number: string; date: string; billedTo: string; from: string; items: { item: string; qty: number; price: number }[]; taxRate: number };
type Statement = { kind: "statement"; account: string; period: string; opening: number; txns: { date: string; desc: string; debit: number; credit: number }[] };
type Doc = Invoice | Statement;

const API = process.env.NEXT_PUBLIC_API_URL || "https://cyber-synth-api.onrender.com";
const COLS: Record<string, [string, string][]> = {
  tabular: [["id", "int"], ["name", "string"], ["email", "string"], ["signup", "date"], ["balance", "decimal"]],
  customers: [["customer_id", "int PK"], ["name", "string"], ["email", "string"]],
  orders: [["order_id", "int PK"], ["customer_id", "int FK"], ["order_date", "date"], ["total", "decimal"]],
  order_items: [["item_id", "int PK"], ["order_id", "int FK"], ["sku", "string"], ["qty", "int"], ["price", "decimal"]],
};

/* ───────── seeded mock generator ───────── */
function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const FIRST = ["Maria", "Ahmed", "Sofia", "Liam", "Aisha", "Noah", "Zara", "Omar", "Elena", "Hiro", "Priya", "Lucas"];
const LAST = ["Chen", "Raza", "Ivanova", "Okafor", "Khan", "Silva", "Novak", "Tanaka", "Haddad", "Meyer", "Rossi", "Singh"];
const MERCH = ["Greenleaf Market", "Riverside Utilities", "Metro Transit", "Blue Kettle Cafe", "Northgate Pharmacy", "Volt Fuel", "StreamBox"];
const SKUS = ["API-PRO", "API-LITE", "ONB-001", "SUP-24H", "STO-100G", "SEC-AUD"];
const pick = <T,>(r: () => number, a: T[]) => a[Math.floor(r() * a.length)];
const pad = (n: number) => String(n).padStart(2, "0");
const dt = (r: () => number) => `2025-${pad(1 + Math.floor(r() * 12))}-${pad(1 + Math.floor(r() * 28))}`;
const money = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD" });
const hash = (s: string) => {
  let h = 5381;
  for (const c of s) h = ((h << 5) + h + c.charCodeAt(0)) >>> 0;
  return h.toString(16).padStart(8, "0");
};
const person = (r: () => number, cfg: Cfg) => {
  const f = pick(r, FIRST), l = pick(r, LAST);
  let name = `${f} ${l}`, email = `${f[0]}.${l}`.toLowerCase() + "@example.com";
  if (cfg.masking) { name = `${f[0]}${"*".repeat(f.length - 1)} ${l[0]}${"*".repeat(l.length - 1)}`; email = `${email[0]}***@example.com`; }
  if (cfg.hashing) email = `${hash(email)}@hash.local`;
  return { name, email };
};
const flag = (r: () => number, cfg: Cfg): "OK" | "NULL" | "OUTLIER" => {
  const x = r() * 100;
  return x < cfg.noise / 2 ? "NULL" : x < cfg.noise ? "OUTLIER" : "OK";
};

function mockTables(mode: Mode, cfg: Cfg): Tables {
  const r = rng(cfg.seed);
  if (mode === "tabular") {
    return {
      tabular: Array.from({ length: cfg.rows }, (_, i) => {
        const s = flag(r, cfg), p = person(r, cfg);
        const base = Math.round(r() * 100000) / 100;
        return { id: 10231 + i, name: p.name, email: s === "NULL" ? null : p.email, signup: dt(r), balance: s === "OUTLIER" ? base * 50 : base, _status: s };
      }),
    };
  }
  const customers: Row[] = Array.from({ length: cfg.rows }, (_, i) => { const p = person(r, cfg); return { customer_id: 1000 + i, name: p.name, email: p.email, _status: "OK" }; });
  const orders: Row[] = [], items: Row[] = [];
  const nOrders = Math.round(cfg.rows * 1.5);
  for (let o = 0; o < nOrders; o++) {
    const s = flag(r, cfg);
    const cust = s === "OUTLIER" ? 9999 : 1000 + Math.floor(r() * cfg.rows); // outlier = orphan FK edge case
    let total = 0;
    const n = 1 + Math.floor(r() * 3);
    for (let k = 0; k < n; k++) {
      const qty = 1 + Math.floor(r() * 5), price = Math.round((20 + r() * 480) * 100) / 100;
      total += qty * price;
      items.push({ item_id: 50000 + items.length, order_id: 5000 + o, sku: pick(r, SKUS), qty, price, _status: "OK" });
    }
    orders.push({ order_id: 5000 + o, customer_id: s === "NULL" ? null : cust, order_date: dt(r), total: Math.round(total * 100) / 100, _status: s });
  }
  return { customers, orders, order_items: items };
}

function mockDoc(kind: DocKind, cfg: Cfg): Doc {
  const r = rng(cfg.seed);
  if (kind === "invoice")
    return {
      kind, number: `INV-${10000 + Math.floor(r() * 9999)}`, date: dt(r), billedTo: "Northwind Supplies Ltd.", from: "Synth Data Co.", taxRate: 0.08,
      items: Array.from({ length: 2 + Math.floor(r() * 3) }, () => ({ item: pick(r, ["API access — Pro tier", "Onboarding support", "Storage add-on", "Security audit", "Priority SLA"]), qty: 1 + Math.floor(r() * 4), price: Math.round((90 + r() * 1100) * 100) / 100 })),
    };
  return {
    kind, account: `**** ${1000 + Math.floor(r() * 8999)}`, period: "Last 90 days", opening: Math.round((800 + r() * 2500) * 100) / 100,
    txns: Array.from({ length: 12 }, (_, i) => {
      const credit = i % 5 === 3;
      return { date: `08-${pad(1 + i * 2)}`, desc: credit ? "Payroll deposit" : pick(r, MERCH), debit: credit ? 0 : Math.round((8 + r() * 140) * 100) / 100, credit: credit ? 2150 : 0 };
    }),
  };
}

/* ───────── helpers ───────── */
const stripPrivate = (rows: Row[]) =>
  rows.map((row) => Object.fromEntries(Object.entries(row).filter(([k]) => !k.startsWith("_"))));
function download(name: string, text: string, type: string) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type }));
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
}
const toCSV = (rows: Row[]) => {
  if (!rows.length) return "";
  const keys = Object.keys(rows[0]);
  return [keys.join(","), ...rows.map((r) => keys.map((k) => JSON.stringify(r[k] ?? "")).join(","))].join("\n");
};

/* ───────── UI atoms ───────── */
const box = "relative border border-emerald-500/30 bg-[#0a0f0d] shadow-[0_0_18px_rgba(0,255,102,0.08)]";
const Badge = ({ s }: { s: string }) => (
  <span className={`px-1.5 py-0.5 text-[10px] border ${s === "OK" ? "text-[#00ff66] border-emerald-500/40" : s === "NULL" ? "text-amber-300 border-amber-400/40" : "text-fuchsia-400 border-fuchsia-500/40"}`}>[{s}]</span>
);
const Field = ({ label, val, children }: { label: string; val?: string | number; children: React.ReactNode }) => (
  <label className="block space-y-1.5">
    <span className="flex justify-between text-[11px] text-emerald-400/70"><span>{label}</span><span className="text-[#00ff66]">{val}</span></span>
    {children}
  </label>
);
const Toggle = ({ label, on, set }: { label: string; on: boolean; set: (v: boolean) => void }) => (
  <button type="button" role="switch" aria-checked={on} onClick={() => set(!on)} className="flex w-full items-center justify-between border border-emerald-500/30 px-3 py-2 text-xs hover:border-[#00ff66]/70 focus-visible:outline focus-visible:outline-1 focus-visible:outline-[#00ff66]">
    <span>{label}</span>
    <span className={on ? "text-[#00ff66] drop-shadow-[0_0_6px_#00ff66]" : "text-emerald-700"}>{on ? "[ ON ]" : "[ OFF ]"}</span>
  </button>
);

/* ───────── page ───────── */
export default function Page() {
  const [mode, setMode] = useState<Mode>("tabular");
  const [cfg, setCfg] = useState<Cfg>({ rows: 100, seed: 42, noise: 5, masking: false, hashing: false });
  const [tables, setTables] = useState<Tables>({});
  const [active, setActive] = useState("customers");
  const [docKind, setDocKind] = useState<DocKind>("invoice");
  const [doc, setDoc] = useState<Doc | null>(null);
  const [sort, setSort] = useState<{ key: string; dir: 1 | -1 } | null>(null);
  const [page, setPage] = useState(0);
  const [busy, setBusy] = useState(false);
  const [src, setSrc] = useState<"MOCK" | "LIVE">("MOCK");
  const [ms, setMs] = useState(24);
  const set = (p: Partial<Cfg>) => setCfg((c) => ({ ...c, ...p }));

  async function call(path: string, body: object) {
    const t = performance.now();
    try {
      const res = await fetch(`${API}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: AbortSignal.timeout(6000) });
      if (!res.ok) throw new Error(String(res.status));
      const data = await res.json();
      setSrc("LIVE"); setMs(Math.round(performance.now() - t));
      return data;
    } catch {
      setSrc("MOCK"); setMs(Math.round(performance.now() - t));
      return null;
    }
  }

  async function generate() {
    setBusy(true); setPage(0); setSort(null);
    if (mode === "documents") {
      const d = await call(`/api/generate/document?doc_type=${docKind}`, {});
      setDoc(d ? (d.document ?? d) : mockDoc(docKind, cfg));
    } else {
      let bodyPayload: any = cfg;
      if (mode === "tabular") {
        const privacyMode = cfg.masking ? "mask" : (cfg.hashing ? "hash" : "none");
        bodyPayload = {
          row_count: cfg.rows,
          seed: cfg.seed,
          null_rate: cfg.noise / 200,
          outlier_rate: cfg.noise / 100,
          fields: [
            { name: "id", type: "uuid", privacy: "none" },
            { name: "name", type: "name", privacy: privacyMode },
            { name: "email", type: "email", privacy: privacyMode },
            { name: "signup", type: "date", privacy: "none" },
            { name: "balance", type: "currency", privacy: "none" }
          ]
        };
      }
      const query = mode === "relational" ? `?cust_count=${Math.min(cfg.rows, 50)}&orders_count=${Math.min(Math.round(cfg.rows * 1.5), 100)}` : "";
      const d = await call(`/api/generate/${mode}${query}`, bodyPayload);
      if (mode === "tabular") setTables({ tabular: d ? (Array.isArray(d) ? d : d.rows) : mockTables("tabular", cfg).tabular });
      else { const t: Tables = d ? (d.tables ?? d) : mockTables("relational", cfg); setTables(t); if (!t[active]) setActive("customers"); }
    }
    setBusy(false);
  }

  // initial preview, then re-generate mock instantly when the mode / doc type changes
  useEffect(() => { generate(); /* eslint-disable-next-line */ }, [mode, docKind]);

  const tableKey = mode === "tabular" ? "tabular" : active;
  const cols = COLS[tableKey] ?? [];
  const rows = tables[tableKey] ?? [];
  const sorted = useMemo(() => {
    if (!sort) return rows;
    return [...rows].sort((a, b) => {
      const x = a[sort.key], y = b[sort.key];
      if (x == null) return 1;
      if (y == null) return -1;
      return (x > y ? 1 : x < y ? -1 : 0) * sort.dir;
    });
  }, [rows, sort]);
  const PS = 10, pages = Math.max(1, Math.ceil(sorted.length / PS));
  const view = sorted.slice(page * PS, page * PS + PS);

  const exportData = (fmt: "csv" | "json" | "pdf") => {
    if (fmt === "pdf") return window.print();
    if (mode === "documents") return doc && (fmt === "json" ? download(`${doc.kind}.json`, JSON.stringify(doc, null, 2), "application/json") : download(`${doc.kind}.csv`, toCSV(doc.kind === "invoice" ? (doc.items as Row[]) : (doc.txns as Row[])), "text/csv"));
    if (fmt === "json") return download(`${mode}.json`, JSON.stringify(mode === "tabular" ? stripPrivate(rows) : Object.fromEntries(Object.entries(tables).map(([k, v]) => [k, stripPrivate(v)])), null, 2), "application/json");
    download(`${tableKey}.csv`, toCSV(stripPrivate(rows)), "text/csv");
  };

  const NAV: [Mode, string][] = [["tabular", "[01 // TABULAR]"], ["relational", "[02 // RELATIONAL]"], ["documents", "[03 // DOCUMENTS]"]];
  const inp = "w-full bg-[#050807] border border-emerald-500/30 px-2 py-1.5 text-sm text-[#00ff66] focus:outline-none focus:border-[#00ff66] focus:shadow-[0_0_10px_rgba(0,255,102,0.35)]";

  return (
    <main className="min-h-screen bg-[#050807] font-mono text-emerald-300 selection:bg-[#00ff66] selection:text-black"
      style={{ backgroundImage: "repeating-linear-gradient(0deg, rgba(0,255,102,0.03) 0 1px, transparent 1px 3px)" }}>
      <style>{`@media print{aside,header,.no-print{display:none!important}main{background:#fff!important}.print-doc{color:#000!important;border:none!important;box-shadow:none!important;background:#fff!important}.print-doc *{color:#000!important;border-color:#999!important}}`}</style>

      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-emerald-500/30 px-4 py-3">
        <h1 className="text-sm tracking-widest text-[#00ff66] drop-shadow-[0_0_8px_#00ff66]">&gt; SYNTH_DATA_PLATFORM<span className="animate-pulse">_</span></h1>
        <span className="text-[11px] text-emerald-400/80">[STATUS: {src === "LIVE" ? "MAINFRAME ONLINE" : "OFFLINE // MOCK FALLBACK"} | {ms}ms]</span>
      </header>

      <div className="grid gap-4 p-4 lg:grid-cols-[220px_minmax(0,1fr)_280px]">
        {/* LEFT RAIL */}
        <aside className={`${box} p-3 lg:self-start`}>
          <p className="mb-3 text-[11px] text-emerald-500/60">// WORKSPACE</p>
          <nav className="flex gap-2 lg:flex-col" aria-label="Data type">
            {NAV.map(([m, l]) => (
              <button key={m} onClick={() => { setMode(m); setPage(0); }} aria-current={mode === m}
                className={`w-full border px-3 py-2 text-left text-xs transition focus-visible:outline focus-visible:outline-1 focus-visible:outline-[#00ff66] ${mode === m ? "border-[#00ff66] bg-emerald-500/10 text-[#00ff66] shadow-[0_0_12px_rgba(0,255,102,0.35)]" : "border-emerald-500/30 text-emerald-400/70 hover:border-emerald-400/60"}`}>
                {l}
              </button>
            ))}
          </nav>
          <p className="mt-4 hidden text-[10px] leading-relaxed text-emerald-500/50 lg:block">Backend: {API}<br />Falls back to local mock data when offline.</p>
        </aside>

        {/* CENTER CANVAS */}
        <section className={`${box} min-w-0 p-4`} aria-live="polite">
          <div className="no-print mb-3 flex flex-wrap items-center justify-between gap-2 text-[11px]">
            <span className="text-[#00ff66]">&gt; LIVE_PREVIEW :: {mode.toUpperCase()}{busy && " :: GENERATING..."}</span>
            {mode === "relational" && (
              <div className="flex gap-1">
                {["customers", "orders", "order_items"].map((t) => (
                  <button key={t} onClick={() => { setActive(t); setPage(0); setSort(null); }} className={`border px-2 py-1 ${active === t ? "border-[#00ff66] text-[#00ff66]" : "border-emerald-500/30 text-emerald-500/70"}`}>{t}</button>
                ))}
              </div>
            )}
            {mode === "documents" && (
              <div className="flex gap-1">
                {(["invoice", "statement"] as DocKind[]).map((k) => (
                  <button key={k} onClick={() => setDocKind(k)} className={`border px-2 py-1 ${docKind === k ? "border-[#00ff66] text-[#00ff66]" : "border-emerald-500/30 text-emerald-500/70"}`}>{k === "invoice" ? "invoice" : "bank statement"}</button>
                ))}
              </div>
            )}
          </div>

          {mode !== "documents" ? (
            <>
              <div className="overflow-x-auto border border-emerald-500/20">
                <table className="w-full text-left text-xs">
                  <thead className="bg-emerald-500/10">
                    <tr>
                      {cols.map(([k, t]) => (
                        <th key={k} className="whitespace-nowrap px-3 py-2 font-normal">
                          <button onClick={() => setSort((s) => (s?.key === k ? { key: k, dir: (s.dir * -1) as 1 | -1 } : { key: k, dir: 1 }))} className="text-left text-[#00ff66] hover:underline">
                            {k}{sort?.key === k ? (sort.dir === 1 ? " ▲" : " ▼") : ""}
                          </button>
                          <div className="text-[10px] text-emerald-500/50">{t}</div>
                        </th>
                      ))}
                      <th className="px-3 py-2 font-normal text-[#00ff66]">status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {view.map((r, i) => (
                      <tr key={i} className="border-t border-emerald-500/10 hover:bg-emerald-500/5">
                        {cols.map(([k, t]) => (
                          <td key={k} className={`whitespace-nowrap px-3 py-1.5 ${t === "decimal" ? "text-right" : ""}`}>
                            {r[k] == null ? <span className="text-amber-300/80">NULL</span> : t === "decimal" ? money(Number(r[k])) : String(r[k])}
                          </td>
                        ))}
                        <td className="px-3 py-1.5"><Badge s={String(r._status ?? "OK")} /></td>
                      </tr>
                    ))}
                    {!view.length && <tr><td colSpan={cols.length + 1} className="px-3 py-6 text-center text-emerald-500/60">No rows yet. Press EXECUTE GENERATION.</td></tr>}
                  </tbody>
                </table>
              </div>
              <div className="no-print mt-3 flex items-center justify-between text-[11px]">
                <span className="text-emerald-500/70">{sorted.length} rows :: page {page + 1}/{pages}</span>
                <div className="flex gap-2">
                  <button disabled={page === 0} onClick={() => setPage(page - 1)} className="border border-emerald-500/30 px-2 py-1 hover:border-[#00ff66] disabled:opacity-30">&lt; PREV</button>
                  <button disabled={page >= pages - 1} onClick={() => setPage(page + 1)} className="border border-emerald-500/30 px-2 py-1 hover:border-[#00ff66] disabled:opacity-30">NEXT &gt;</button>
                </div>
              </div>
            </>
          ) : doc ? (
            <DocView doc={doc} />
          ) : (
            <p className="py-10 text-center text-xs text-emerald-500/60">No document yet. Press EXECUTE GENERATION.</p>
          )}
        </section>

        {/* RIGHT RAIL */}
        <aside className={`${box} space-y-4 p-4 lg:self-start`}>
          <p className="text-[11px] text-emerald-500/60">// CONFIGURATION</p>
          <Field label="ROW_COUNT" val={cfg.rows}>
            <input type="range" min={10} max={1000} step={10} value={cfg.rows} onChange={(e) => set({ rows: +e.target.value })} className="w-full accent-[#00ff66]" />
          </Field>
          <Field label="RANDOM_SEED">
            <input type="number" value={cfg.seed} onChange={(e) => set({ seed: +e.target.value || 0 })} className={inp} />
          </Field>
          <Field label="NOISE / OUTLIER_RATE" val={`${cfg.noise}%`}>
            <input type="range" min={0} max={50} value={cfg.noise} onChange={(e) => set({ noise: +e.target.value })} className="w-full accent-[#00ff66]" />
          </Field>
          <div className="space-y-2">
            <p className="text-[11px] text-emerald-400/70">PRIVACY_RULES</p>
            <Toggle label="Masking" on={cfg.masking} set={(v) => set({ masking: v })} />
            <Toggle label="Hashing" on={cfg.hashing} set={(v) => set({ hashing: v })} />
          </div>
          <button onClick={generate} disabled={busy}
            className="w-full border border-[#00ff66] bg-[#00ff66]/10 py-3 text-sm font-bold tracking-widest text-[#00ff66] shadow-[0_0_20px_rgba(0,255,102,0.5)] transition hover:bg-[#00ff66] hover:text-black hover:shadow-[0_0_32px_rgba(0,255,102,0.85)] disabled:opacity-50">
            {busy ? "GENERATING..." : "EXECUTE GENERATION"}
          </button>
          <div className="space-y-2 border-t border-emerald-500/20 pt-4">
            <p className="text-[11px] text-emerald-400/70">EXPORT DATA</p>
            <div className="grid grid-cols-3 gap-2">
              {(["csv", "json", "pdf"] as const).map((f) => (
                <button key={f} onClick={() => exportData(f)} className="border border-emerald-500/30 py-1.5 text-xs uppercase hover:border-[#00ff66] hover:text-[#00ff66] hover:shadow-[0_0_10px_rgba(0,255,102,0.35)]">{f}</button>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}

/* ───────── document preview ───────── */
function DocView({ doc }: { doc: Doc }) {
  if (doc.kind === "invoice") {
    const sub = doc.items.reduce((s, i) => s + i.qty * i.price, 0), tax = sub * doc.taxRate;
    return (
      <article className="print-doc mx-auto max-w-2xl border border-emerald-500/30 bg-[#050807] p-5 text-sm">
        <div className="flex justify-between border-b border-emerald-500/20 pb-3"><h2 className="tracking-widest text-[#00ff66]">INVOICE</h2><span className="text-emerald-500/70">#{doc.number}</span></div>
        <div className="my-4 flex justify-between text-xs"><div><p className="text-emerald-500/60">BILLED TO</p><p>{doc.billedTo}</p></div><div className="text-right"><p className="text-emerald-500/60">FROM</p><p>{doc.from}</p><p className="text-emerald-500/60">{doc.date}</p></div></div>
        <div className="overflow-x-auto"><table className="w-full text-xs">
          <thead className="bg-emerald-500/10 text-[#00ff66]"><tr><th className="p-2 text-left font-normal">Item</th><th className="p-2 text-right font-normal">Qty</th><th className="p-2 text-right font-normal">Price</th><th className="p-2 text-right font-normal">Amount</th></tr></thead>
          <tbody>{doc.items.map((i, k) => <tr key={k} className="border-t border-emerald-500/10"><td className="p-2">{i.item}</td><td className="p-2 text-right">{i.qty}</td><td className="p-2 text-right">{money(i.price)}</td><td className="p-2 text-right">{money(i.qty * i.price)}</td></tr>)}</tbody>
        </table></div>
        <div className="mt-4 space-y-1 text-right text-xs"><p>Subtotal: {money(sub)}</p><p>Tax ({doc.taxRate * 100}%): {money(tax)}</p><p className="text-base text-[#00ff66] drop-shadow-[0_0_6px_#00ff66]">Total: {money(sub + tax)}</p></div>
      </article>
    );
  }
  let bal = doc.opening;
  const lines = doc.txns.map((t) => ({ ...t, bal: (bal = bal - t.debit + t.credit) }));
  return (
    <article className="print-doc mx-auto max-w-2xl border border-emerald-500/30 bg-[#050807] p-5 text-sm">
      <div className="flex justify-between border-b border-emerald-500/20 pb-3"><h2 className="tracking-widest text-[#00ff66]">BANK STATEMENT</h2><span className="text-emerald-500/70">{doc.account}</span></div>
      <p className="my-3 text-xs text-emerald-500/70">{doc.period} :: opening balance {money(doc.opening)}</p>
      <div className="overflow-x-auto"><table className="w-full text-xs">
        <thead className="bg-emerald-500/10 text-[#00ff66]"><tr><th className="p-2 text-left font-normal">Date</th><th className="p-2 text-left font-normal">Description</th><th className="p-2 text-right font-normal">Debit</th><th className="p-2 text-right font-normal">Credit</th><th className="p-2 text-right font-normal">Balance</th></tr></thead>
        <tbody>{lines.map((l, k) => <tr key={k} className="border-t border-emerald-500/10"><td className="p-2">{l.date}</td><td className="p-2">{l.desc}</td><td className="p-2 text-right">{l.debit ? money(l.debit) : ""}</td><td className="p-2 text-right text-[#00ff66]">{l.credit ? money(l.credit) : ""}</td><td className="p-2 text-right">{money(l.bal)}</td></tr>)}</tbody>
      </table></div>
    </article>
  );
}
