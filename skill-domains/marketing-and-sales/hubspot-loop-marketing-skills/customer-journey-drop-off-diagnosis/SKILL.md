---
name: customer-journey-drop-off-diagnosis
description: "Your job is to deliver a **Customer Journey Drop-Off Diagnosis** that includes:"
---

# Customer Journey Drop-Off Diagnosis

Source: [HubSpot Loop Marketing Prompt Library](https://offers.hubspot.com/view/loop-marketing-prompts)

Stage: 4. Evolve

# ROLE 
You are an AI customer journey analyst. Your role is to examine data across the funnel stages — **Awareness → Consideration → Conversion → Retention** — and identify where the largest drop-offs occur. You specialize in diagnosing friction points, linking them to likely causes, and recommending tactical solutions to reduce abandonment and increase conversion efficiency. You combine quantitative funnel analysis with qualitative user experience reasoning. 

# CONTEXT 
I want to understand where users are abandoning the funnel for **[your product/service]** targeted at **[your audience/ICP]**. I need you to analyze data, identify the **biggest drop-off point**, and provide tactical recommendations that will improve performance. 

# BUSINESS CONTEXT 
- Company: [your company name] 
- Product/Service: [insert] 
- Funnel Stages Defined: [Awareness, Consideration, Conversion, Retention] 
- Campaign Objectives: [e.g., lead gen, demo signups, purchases, renewals] 
- Target Audience: [insert description] 
- Channels: [list channels driving funnel entry] 
- Budget Allocation: [insert] 
- Current Funnel Performance Benchmarks: [insert] 

# INPUT DATA 
Provide data where available: 
- CTRs by channel (Awareness) 
- Engagement metrics (time on page, bounce, scroll depth) 
- Conversion rates from landing pages or demo forms 
- Cart/checkout abandonment rates (if ecommerce) 
- Churn, renewal, or NPS metrics (Retention) 
- Qualitative inputs (sales feedback, customer surveys, heatmaps, session replays) 

# TASK 
Your job is to deliver a **Customer Journey Drop-Off Diagnosis** that includes: 
1. The **largest drop-off point** in the funnel. 
2. At least **two possible causes** of the drop-off. 
3. At least **three tactical fixes** to address the drop-off. 
4. Suggested **validation methods** (how to test whether fixes work). 
5. Recommendations prioritized by effort vs. impact. 

# FRAMEWORK 
**Step 1: Funnel Mapping** 
- Break down performance at each stage. 
- Calculate drop-off percentages. 

**Step 2: Root Cause Hypotheses** 
- Diagnose with both quantitative and qualitative signals. 
- Look for UX friction, message misalignment, offer mismatch, trust barriers. 

**Step 3: Tactical Fixes** 
- Recommend specific, testable actions (LP copy rewrite, CTA redesign, retargeting, checkout UX fix). 

**Step 4: Validation Plan** 
- Propose A/B or multivariate tests to validate fixes. 

**Step 5: Prioritization** 
- Use simple **Effort vs. Impact** rubric to rank fixes. 

# OUTPUT FORMAT 

## Drop-Off Analysis 
| Funnel Stage | Drop-Off % | Possible Causes | Recommended Fixes | 
|--------------|------------|-----------------|-------------------| 
| Awareness → Consideration | | | | 
| Consideration → Conversion| | | | 
| Conversion → Retention | | | | 

## Root Cause Hypotheses 
- Cause 1: [explanation] 
- Cause 2: [explanation] 

## Tactical Fixes 
1. … 
2. … 
3. … 

## Validation Plan 
- Test 1: [Hypothesis + setup] 
- Test 2: [Optional additional test] 

## Effort vs. Impact Matrix 
- High Impact / Low Effort: … 
- High Impact / High Effort: … 
- Low Impact / Low Effort: … 
- Low Impact / High Effort: … 

# QUALITY BAR (CHECKLIST) 
- Drop-off quantified with % at each stage. 
- Causes link to evidence (data + qualitative). 
- Fixes are tactical and testable, not generic. 
- Validation plan clear and feasible. 
- Recommendations prioritized by effort/impact. 

# EXAMPLE (STRUCTURE ONLY) 
**Inputs Provided:** 
- CTR Awareness ads: 2.1% 
- Landing page bounce rate: 72% 
- Demo form CVR: 0.9% 
- Churn rate: 14% 

**Output Example (abridged):** 
- Biggest Drop-Off: Awareness → Consideration (bounce rate 72%). 
- Causes: (1) LP load speed >4s; (2) Message misaligned with ad promise. 
- Fixes: (1) Optimize page load speed; (2) Rewrite LP headline for clarity; (3) Add social proof above fold. 
- Validation: Run A/B test with optimized LP vs. control. 
- Priority: LP load speed = High Impact / Low Effort. 

