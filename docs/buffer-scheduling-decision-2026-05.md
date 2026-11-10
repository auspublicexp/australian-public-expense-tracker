# Buffer scheduling decision and initial queue setup (May 2026)

> Historical workflow note. This records the early Buffer setup discussion, not a verified description of current account settings or an obligation to post at a fixed rate. The [editorial policy](editorial-social-media-policy.md) takes precedence.

## Tool selection

APET chose Buffer as a practical, low-maintenance way to schedule prepared chart-and-caption posts to its X account (`@auspublicexp`). The maintainer indicated an intention to sign up for a plan described at the time as USD 60/year with an unlimited posting queue. This was the user's understanding of the offer, **not an independently verified price, entitlement, or proof of purchase**. Check Buffer's current pricing and plan limits before relying on it.

Typefully and Metricool were considered alternatives; Buffer was preferred for simple queue management, chart image support and a human-reviewed publishing process. No X API integration or automatic publication by chart-generation scripts was required.

## How the queue was intended to work

In Buffer's composer, **Next Available** places a post in the next available scheduled queue slot; it does not mean publish immediately. Other options visible at the time included **Prioritize**, **Now**, and **Set Date and Time**.

The initial **proposed** Australian audience slots were:

- 7:30 am Australian Eastern time — morning news/commute
- 12:30 pm Australian Eastern time — lunch
- 7:30 pm Australian Eastern time — evening

These were untested suggestions, not engagement findings or confirmed configured slots. Set an explicit Australian timezone in Buffer and account for daylight saving (AEST versus AEDT) rather than assuming a fixed UTC offset. Review actual audience analytics before optimizing times. Three posts daily was a possible starting experiment, **not a quota**; publish fewer when the material does not warrant it.

## Publishing process

1. Generate charts and supporting verification data from official sources.
2. Review each chart, reporting period, factual caption, terminology, limitations and source attribution.
3. Upload the approved chart and caption to Buffer and place it in a queue slot or set a specific date/time.
4. Rotate topics rather than publishing many near-identical charts from one quarter consecutively.
5. Record the published X URL and relevant metadata in the posting log. A Buffer draft or queued item is not evidence of publication.

The screenshot discussed showed a Jan–Mar 2024 IPEA state/territory spending chart and a draft caption saying NSW had the highest reported expenditure, followed by Victoria and Queensland. **That ranking was not independently verified in this scheduling discussion**, so the screenshot and caption should not be treated as an authoritative data finding.

## Guardrails

The APET website remains the primary data archive; social media is a selective editorial layer. Keep source checking and final human approval separate from chart generation. Do not infer that all prepared charts should be published, or that a full queue takes priority over relevance and accuracy. See [editorial and social-media policy](editorial-social-media-policy.md).
