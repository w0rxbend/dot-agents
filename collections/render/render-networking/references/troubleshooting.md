# Private network troubleshooting

## DNS resolution failures

- Confirm both services share **same region** and **same workspace**. Private DNS is scoped to that pair.
- Verify **target service is running** (deploy succeeded, process up). Stopped or failed deploys will not resolve usefully.

## Port conflicts and limits

- **Reserved ports:** **18012**, **18013**, **19099** — do not use for primary listener. (**10000** is not reserved: it is usual default value of `PORT`, which web services should bind.)
- **75-port maximum** per service; at cap, trim or consolidate listeners.
- **Multi-port Web Services:** Only **`PORT`** port gets **public** HTTP; other open ports are **private-only**. Callers on wrong port, or expecting public routing on extra port, fail or time out.

## Cross-region

Services in **different regions** **cannot** communicate over Render’s private network. Use public endpoints, data replication, or move peers into one region.

## Cross-workspace

Services in **different workspaces** **cannot** communicate privately, even with matching regions. Merge into one workspace or use allowed public/integration path.

## Protocol mismatches

- Some HTTP clients need explicit **`http://`** or **`https://`** prefix on internal URLs; bare hostname may not form valid request URL.
- **TLS** mismatch (HTTPS client to HTTP server or reverse) gives connection errors that look like “network” failures.

## Free-tier limitations

**Free Web Services** can **send** private traffic but **cannot receive** inbound private connections. If Private Service or another Web Service cannot privately reach free-tier web target, upgrade target or use different topology (e.g., public API with auth).

## Workers, crons, and workflows “unreachable”

**Background Workers**, **Cron Jobs**, and **Workflow Runs** have **no internal hostname** and **cannot** accept inbound private connections. Only **outbound** calls from them work; do not point other services at “worker internal URL.”

## DNS resolver

- Use runtime’s **system DNS** (e.g., behavior consistent with **`/etc/resolv.conf`** in Linux containers).
- Avoid custom HTTP-based lookups for internal Render names; they bypass platform’s private DNS chain.

## Environment isolation (Professional+)

If private traffic between previously working services **suddenly fails**, check whether **per-environment isolation** was enabled or tightened. Isolation can **block cross-environment** private traffic even when region and workspace match.

## Static sites

**Static Sites are not on private network.** They cannot call or be called via internal hostnames. Integrate through Web Service or edge-appropriate public API.
