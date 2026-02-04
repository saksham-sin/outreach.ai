# Outreach.ai

👉 **Live App:** https://app.outreachai-demo.online

A production-ready Mini-SaaS for AI-powered email outreach.
Built for sales teams and SDRs to run reliable, personalized cold email campaigns without the overhead of enterprise tooling.

---

## What This Is

Cold outreach at scale is manual and error-prone. Sales teams juggle inboxes, spreadsheets, and reminders, often losing track of what was sent, when follow-ups are due, and who has already replied.

Outreach.ai is **not an email client**. It is a system for **running outbound campaigns end-to-end** — with AI-assisted personalization, scheduled follow-ups, and inbound reply detection that automatically stops sequences when a prospect responds.

This was built as a hosted Mini-SaaS rather than a script because campaigns are stateful, replies require webhooks, and reliability matters.

---

## Core Workflow (Happy Path)

1. Sign in using a magic link (no passwords)
2. Create a campaign
3. Import leads (CSV-based for v1)
4. Write or generate an email template
5. Schedule the campaign
6. Emails send automatically
7. Follow-ups trigger on time
8. Replies immediately halt future follow-ups

The system is intentionally constrained. One campaign, one sequence, predictable behavior.

---

## Key Product Decisions

### Email-Only for v1

Email was chosen deliberately:
- Highest ROI channel for outbound
- Most compliance-sensitive
- Stable compared to platform-dependent channels

Depth over breadth.

---

### Magic Links Instead of Passwords

Magic links reduce friction and infrastructure complexity:
- No password storage
- No reset flows
- Smaller attack surface

This fits a self-serve SaaS with known users.

---

### One Signature Per User

A single signature keeps the model simple and covers most use cases. Per-template signatures add cognitive and data-model complexity without meaningful upside.

---

### Minute-Level Scheduling

Minute-level scheduling exists primarily to enable fast demos and testing. In production usage, campaigns can still be spaced hourly or daily.

Supporting finer granularity surfaces edge cases early without constraining real usage.

---

## Handling Follow-ups Safely ("Waiting" Problem)

Follow-ups should never send after a reply arrives.

The system guarantees this by:
- Persisting every scheduled send in the database
- Checking reply state immediately before sending
- Skipping and marking jobs complete if a reply exists

The database is the source of truth. No distributed locks, no queues, no race conditions.

---

## AI Usage

AI is used selectively:
- Personalizing email bodies
- Generating a user signature

AI is *not* used for scheduling, reply detection, or scoring. Those remain deterministic.

Generation happens synchronously so users can see and approve output before saving.

---

## Email Delivery & Reply Detection

**This is a fully functional, end-to-end system with no simulation.**

Emails are sent via **Resend** and delivered to real inboxes. Inbound replies are handled via webhooks. When a reply is received:
- The lead is marked complete
- All pending follow-ups are halted immediately

No inbox polling. No heuristics. No test mode.

---

## Architecture (High-Level)

- **Frontend:** React + TypeScript + Vite
- **Backend:** FastAPI
- **Background Worker:** scheduling, retries, dispatch
- **Database:** PostgreSQL

The system favors clarity and debuggability over infrastructure complexity.

---

## UI Philosophy

The UI is intentionally simple and workflow-focused.

This aligns with the expectation that the system could later be integrated into **Prosp.ai**, where branding and visual polish would be handled at the platform level.

---

## What’s Intentionally Out of Scope

- Multi-channel outreach
- A/B testing
- Analytics dashboards
- Per-user sending domains
- Rate limiting

The focus is the core loop: **create → send → wait → stop on reply**.

---

## Demo

Reviewers can log in with any email, create a campaign, send real emails, and reply to see follow-ups stop automatically.

---

## Closing Note

This project prioritizes judgment over breadth.

The goal was to ship a small, reliable system that behaves predictably under real conditions — and to stop once the happy path was solid.