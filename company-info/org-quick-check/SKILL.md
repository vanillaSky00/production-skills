---
name: org-quick-check
description: 5-minute credibility snapshot of the company, org, or maintainer behind a blog, open-source project, or tool. Use when the user asks "who's behind this?", "is this org legit/influential?", or shares a link and wants a quick status check.
---

# Org Quick Check

Goal: a fast mental model of who is behind a resource, not a research report.
Time budget: ~5 minutes, 3–5 searches max.

## Steps
1. **Identify the owner** — company, foundation, research lab, or individual maintainer behind the link.
2. **Look up 3 things:**
   - **Established** — founding year, age of the org or project
   - **Money / scale** — funding raised, valuation or revenue, headcount. For OSS: foundation backing (CNCF, Apache, Linux Foundation), corporate sponsor, GitHub stars, contributors
   - **People** — founders or core maintainers: where they worked or studied, notable prior projects
3. **Sources to prefer:** official About / team page, Crunchbase, LinkedIn, Wikipedia, GitHub org page, recent news. Skip deep dives.

## Output
Keep it under 10 lines:

| Item | Finding |
|---|---|
| Who | |
| Founded | |
| Funding / scale | |
| Key people | |
| Signal | 🟢 established / 🟡 emerging / 🔴 unknown or weak |

**One-line take:** why it's worth trusting (or what to be careful about).

Mark anything not found as "not found" — don't guess.

Put the files in companies/, with <lowercase_company_name>.md
