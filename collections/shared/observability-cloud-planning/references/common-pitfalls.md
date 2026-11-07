# Common Pitfalls

- **Problem:** static mapping described as completed workspace build.
  **Solution:** deliver manual mappings without connection. Claim live change only after
  authorized tool operation succeeds.
- **Problem:** all five questions asked in one message.
  **Solution:** ask one, wait, drop any that first answer covered.
- **Problem:** uptime check on same server as site.
  **Solution:** monitor from outside, ideally from different provider or region.
  Self-hosted check cannot observe own failure.
- **Problem:** monitoring server, not booking.
  **Solution:** add synthetic check completing real transaction end to end. That signal
  matches business loss.
- **Problem:** twenty alerts, none read.
  **Solution:** three signals, `Critical` only for waking someone, quarterly review deleting
  anything no human acted on. Alert fatigue is not tooling problem.
- **Problem:** SLO of 99.99% on business never measured above 98%.
  **Solution:** measure baseline, then set target you can hold. Permanently firing alert is
  a target that already failed.
- **Problem:** alert with no runbook, discovered at 3am.
  **Solution:** blank `Runbook URL` blocks going live. Write runbook first; rehearse while
  site is up.
- **Problem:** whole stack arrived at once; nothing maintained after month two.
  **Solution:** phase it. Phase 2 only when phase 1 is read and acted on.
- **Problem:** logs shipped to third party, including personal data and card fragments.
  **Solution:** decide what may leave business before installing agent, not after. Scrub at
  source.
- **Problem:** December arrived; plan never tested under load.
  **Solution:** test in November. Peak season is the one time monitoring plan must already
  be proven.
- **Problem:** service with no named owner.
  **Solution:** assign one. Unowned service is unmonitored regardless of dashboards.
- **Problem:** all four artifacts drift apart.
  **Solution:** derive all four from field list in this file, never by hand.
- **Problem:** Notion import shows every column as Text.
  **Solution:** expected. Apply property mapping table once, after import.


See [Related Skills](related-skills.md) for full guidance.
