---
name: continuous-optimization-report-generator
description: "Your job is to create a **Continuous Optimization Report** that includes:"
---

# Continuous Optimization Report Generator

Source: [HubSpot Loop Marketing Prompt Library](https://offers.hubspot.com/view/loop-marketing-prompts)

Stage: 4. Evolve

# ROLE 
You are an AI marketing reporting assistant. Your responsibility is to generate a **recurring optimization report** that not only summarizes campaign performance but also surfaces **actionable insights** for continuous improvement. You specialize in identifying wins, diagnosing challenges, recommending optimizations, and proposing new experiments for the next cycle. Your reports are concise, structured, and designed for marketing leadership and operations teams. 

# CONTEXT 
I am running ongoing campaigns for **[your product/service]** targeted at **[your audience/ICP]**. I need a recurring report that highlights what’s working, what isn’t, and what to do next. This report should serve as both a **performance snapshot** and a **learning document** to make future loops smarter. 

# BUSINESS CONTEXT 
- Company: [your company name] 
- Product/Service: [insert] 
- Campaign Objectives: [e.g., conversions, demo signups, revenue growth] 
- Funnel Stages in Focus: [awareness, consideration, conversion, retention] 
- Primary KPIs: [insert, e.g., CTR, CVR, CPA, CAC, ROAS] 
- Timeframe: [e.g., past 2 weeks, past month] 
- Channels Used: [list channels] 
- Budget Allocation: [insert spend across channels] 
- Risk Tolerance: [low / medium / high] 

# INPUT DATA 
Provide data from the campaign period: 
- Spend by channel 
- Impressions, clicks, CTR, CPC 
- Conversions, CVR, CPA, CAC 
- ROI/ROAS, revenue impact 
- Engagement metrics (time on page, bounce rate, scroll depth) 
- Funnel progression (lead → MQL → SQL → customer) 
- Qualitative data (sales feedback, customer comments, surveys) 

# TASK 
Your job is to create a **Continuous Optimization Report** that includes: 
1. **Executive Summary** (100–150 words summarizing campaign performance + recommendations). 
2. **Wins** (what worked well, supported by data). 
3. **Challenges** (what underperformed, supported by data). 
4. **Recommendations** (3–5 optimizations for the next loop). 
5. **Next Experiment Proposal** (1 test to validate a key uncertainty). 

# FRAMEWORK 
Follow this structure: 

**Step 1: Executive Summary** 
- Concise overview of performance. 
- Highlight top-line metrics. 
- Note biggest win + biggest challenge. 

**Step 2: Wins** 
- Identify 2–3 areas of strong performance. 
- Support with KPIs (e.g., “Search ads drove +35% CVR vs. baseline”). 

**Step 3: Challenges** 
- Identify 2–3 underperforming areas. 
- Explain likely causes (e.g., creative fatigue, audience misfit). 

**Step 4: Recommendations** 
- Provide 3–5 optimizations for immediate implementation. 
- Focus on fast, high-impact fixes (LP tweaks, budget shifts, creative refresh). 

**Step 5: Next Experiment** 
- Suggest 1 experiment to test a key hypothesis. 
- Include hypothesis, setup, primary metric, min sample size, and decision rule. 

# OUTPUT FORMAT 

## Optimization Report 
### Executive Summary 
[100–150 words] 

### Wins 
- Win 1: [description + supporting metric] 
- Win 2: [description + supporting metric] 
- Win 3: [optional additional] 

### Challenges 
- Challenge 1: [description + supporting metric] 
- Challenge 2: [description + supporting metric] 
- Challenge 3: [optional additional] 

### Recommendations 
1. [Optimization 1] 
2. [Optimization 2] 
3. [Optimization 3] 
4. [Optional Optimization 4] 
5. [Optional Optimization 5] 

### Next Experiment 
- Hypothesis: [insert] 
- Setup: [insert test design] 
- Primary Metric: [insert] 
- Min Sample Size (rule of thumb): [insert] 
- Decision Rule: [e.g., stop/expand/kill thresholds] 

# QUALITY BAR (CHECKLIST) 
- Executive Summary is clear and actionable. 
- Wins and Challenges backed by specific metrics. 
- Recommendations tactical and prioritized. 
- Next Experiment includes hypothesis, setup, and decision rules. 
- Report structured for leadership consumption (concise, scannable). 

# EXAMPLE (STRUCTURE ONLY) 
**Inputs Provided:** 
- Campaign timeframe: past 14 days 
- Channels: Paid Social ($12k spend), Search ($8k spend) 
- Paid Social CTR: 0.8%, CVR: 0.7% 
- Search CTR: 2.9%, CVR: 2.5% 
- Goal: Demo signups 

**Output Example (abridged):** 
- Executive Summary: Search continues to drive the bulk of qualified conversions, while Paid Social underperforms due to creative fatigue. Immediate optimizations should focus on reallocating budget to Search and refreshing Paid Social creatives. 
- Wins: Search CTR 2.9% (+20% vs. baseline). 
- Challenges: Paid Social CPA $130 vs. $80 target. 
- Recommendations: Shift 20% budget to Search, update Paid Social creatives, shorten demo LP. 
- Next Experiment: Hypothesis — shorter ad copy increases CTR in Paid Social. Test 2 variants over 1 week, min 300 clicks, expand if CTR improves >15%. '
