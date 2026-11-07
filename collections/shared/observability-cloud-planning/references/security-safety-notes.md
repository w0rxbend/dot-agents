# Security & Safety Notes

- Never invent hostname, IP address, service identifier, provider, price, traffic figure,
  error rate, uptime percentage or recovery time. `Unknown` and blank are correct.
- Never paste credentials, API keys, tokens, SSH keys, database connection strings, backup
  locations or `.env` contents into this table. Not into dashboard field, not into Notes.
- Never paste real customer, personal, health or payment data into this table.
  `Data Handled` records the *category*, not the data.
- Do not put secrets, tokens or personal data in log lines. Logging configuration makes
  that decision; this table records consequence. Service that would log secrets needs
  different design.
- Sending logs to third-party service is data transfer. Confirm destination, agreement,
  region and retention before enabling. Record decision in `Notes`.
- `Data Handled` = `Credentials or secrets` makes access to those logs itself privileged.
  Restrict it and review who has it.
- Never leave monitoring endpoint unauthenticated. Public status page leaking internal
  hostnames or error detail is information disclosure.
- Alert channels contain contact details. Keep register access-restricted. Do not paste
  real phone number or escalation tree into shared spreadsheet while prototyping.
- If monitoring tool gets production access, scope it to read-only and minimum needed.
  Observability agent with write access to what it observes is real privilege.
- Local reads, generation commands, and validation are part of requested artifact build.
  External writes, messages, provisioning, and publication need authorization for that
  action and target. Existing explicit authorization need not be repeated.


See [Common Pitfalls](common-pitfalls.md) for full guidance.
