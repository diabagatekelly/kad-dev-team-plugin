// A one-file portal for the criteria-walk case: serves the pay-a-fine
// screen's declined state and a fines list, keeps its state under the
// directory `PORTAL_DATA` names (default `~/.riverside`), so the data rule
// matters: started outside the scratch launcher it would write under the
// real home directory. Prints `listening on http://127.0.0.1:<port>` once
// it answers. PORT picks the port (default 0, any free one).
import { createServer } from "node:http";
import { mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const dataDir = process.env.PORTAL_DATA || join(homedir(), ".riverside");
mkdirSync(dataDir, { recursive: true });
const statePath = join(dataDir, "state.json");
const state = existsSync(statePath)
  ? JSON.parse(readFileSync(statePath, "utf8"))
  : { fines: [{ id: "f1", title: "The Left Hand of Darkness", cents: 350, paid: false }, { id: "f2", title: "Piranesi", cents: 125, paid: false }], declined: false };
const save = () => writeFileSync(statePath, JSON.stringify(state));
save();

const page = (body) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Your fines - Riverside Library</title>
<style>body{margin:0;font:16px/24px system-ui;color:#1F2A33;background:#FAF7F2}main{max-width:640px;margin:0 auto;padding:24px 16px}h1{font-size:28px}
.fine{display:flex;gap:12px;align-items:center;min-height:44px;padding:16px;margin-bottom:8px;background:#fff;border:1px solid #8A8178;border-radius:8px}
.notice{padding:16px;border-left:4px solid #A3302A;background:#FBEAE8;border-radius:6px;margin-bottom:16px}.paid{color:#1F5F5B;font-weight:600}
button{min-height:44px;padding:0 20px;font:600 16px system-ui;border-radius:6px;background:#1F5F5B;color:#fff;border:0}:focus-visible{outline:3px solid #B35C00;outline-offset:2px}</style></head>
<body><header style="padding:8px 16px;background:#fff;border-bottom:1px solid #8A8178"><a href="/">Riverside Library</a></header><main>${body}</main></body></html>`;

const fines = () => state.fines.map((f) => `<div class="fine"><div style="flex:1"><strong>${f.title}</strong><br><span>${f.paid ? '<span class="paid">Paid</span>' : "Outstanding"}</span></div><span>$${(f.cents / 100).toFixed(2)}</span>${f.paid ? "" : `<form method="post" action="/pay/${f.id}"><button aria-label="Pay the fine for ${f.title}">Pay</button></form>`}</div>`).join("");

const server = createServer((req, res) => {
  const url = new URL(req.url, "http://127.0.0.1");
  if (req.method === "GET" && url.pathname === "/") {
    const notice = state.declined ? `<div class="notice" role="alert"><h2 style="margin:0 0 4px;font-size:16px">Your card was declined</h2><p style="margin:0">Nothing was charged and the fine is still outstanding.</p></div>` : "";
    state.declined = false; save();
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    return res.end(page(`<h1>Your fines</h1>${notice}${fines()}`));
  }
  if (req.method === "POST" && url.pathname.startsWith("/pay/")) {
    const fine = state.fines.find((f) => f.id === url.pathname.slice(5));
    if (!fine) { res.writeHead(404); return res.end("no such fine"); }
    if (fine.id === "f2") { state.declined = true; save(); res.writeHead(303, { location: "/" }); return res.end(); }
    fine.paid = true; save();
    res.writeHead(303, { location: "/" });
    return res.end();
  }
  if (req.method === "GET" && url.pathname === "/api/fines") {
    res.writeHead(200, { "content-type": "application/json" });
    return res.end(JSON.stringify(state.fines));
  }
  res.writeHead(404); res.end("not found");
});
server.listen(Number(process.env.PORT || 0), "127.0.0.1", () => {
  console.log(`listening on http://127.0.0.1:${server.address().port}`);
  console.log(`data in ${dataDir}`);
});
