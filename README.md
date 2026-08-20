# FraudShield — UPI Payment Fraud Detection

A working prototype of a fraud-screening engine for **UPI payment screenshots** sent over
WhatsApp. Built as a single self-contained HTML file — no build step, no server, no
internet connection required.

> **[▶ Open the prototype](fraud-detection-prototype.html)** — download the file and
> double-click it, or clone the repo and open it in any browser.

---

## The problem

Across India, small businesses and collection agents — kirana shops, milk vendors, EMI
collection agents, cooperative credit societies — accept UPI payments and take a
**WhatsApp screenshot as proof**. There is no automated verification anywhere in that
loop, which makes it trivially exploitable:

| Attack | How it works |
|---|---|
| **Edited screenshot** | Amount or status digits altered in an image editor |
| **Screenshot replay** | One genuine screenshot forwarded to several different vendors |
| **Wrong payee VPA** | Screenshot is 100% genuine — the money went to a *different* UPI ID |
| **Stale transaction** | A real payment from three weeks ago presented as today's |
| **Fabricated reference** | A made-up UTR that matches no real transaction |

Enterprise fraud platforms (FICO Falcon, NICE Actimize, Sift) target large banks and
payment processors. Nothing in that tier is priced or scoped for a collection agent
handling forty payments a day.

---

## What this prototype does

Feed it a payment claim — a screenshot plus the extracted fields — and it returns an
**explainable risk verdict** in under a second.

- **Risk score 0–100** from a weighted rule engine
- **Green / Yellow / Red** verdict with an explicit threshold
- **Per-rule breakdown** — every check states why it passed or failed
- **Transaction ledger** with severity striping and verdict filters
- **Fraud analytics** — which rule is catching what, and repeat-offender tracking

Four one-click demo cases are built in (genuine, replay, wrong VPA, edited amount), and
you can upload a real screenshot or edit any extracted field to drive the engine yourself.

### Verdict thresholds

| Score | Verdict | Action |
|---|---|---|
| 0 – 24 | 🟢 **Green** | Auto-accept |
| 25 – 49 | 🟡 **Yellow** | Manual review |
| 50 – 100 | 🔴 **Red** | Block + alert |

---

## The rule engine

Eight weighted rules. A rule fires when its **fraud condition** is present, and its weight
is added to the risk score.

| ID | Rule | Detects | Weight |
|---|---|---|---|
| R1 | UTR reuse detection | Same reference number claimed twice | 60 |
| R2 | Exact file duplicate | Identical image file forwarded again | 55 |
| R3 | Payee VPA verification | Money sent to a different UPI ID | 55 |
| R4 | Amount integrity check | Edited or mismatched amount | 45 |
| R5 | UTR format validation | Fabricated reference number | 30 |
| R6 | Timestamp freshness | Old transaction reused as new | 20 |
| R7 | Payer velocity check | Unusual submission frequency | 15 |
| R8 | Bank settlement match | No real money received | 30 |

Weights are calibrated so that **any single critical rule (R1–R3) pushes the score into
Red on its own**, while softer signals only escalate in combination.

R8 models the difference between the two deployment modes:

- **Flow A** — no payment gateway connected. R8 always fires (+30), so the best
  achievable verdict is Yellow. The system can prove a claim is *bad*, never that it's *good*.
- **Flow B** — gateway connected. The UTR is matched against real settlement data, and a
  clean claim reaches Green.

Toggle **"Payment gateway connected"** in the UI to see the same transaction move between
the two modes.

---

## Key finding: why perceptual hashing does not work here

The first design used a **perceptual hash** (pHash / aHash / dHash) to detect re-sent
screenshots — the standard textbook approach. It was implemented, measured, and
**disproved**.

A perceptual hash downscales an image to a small grid, so what it really encodes is
**layout**. Every UPI success screen from the same app has an identical layout. The only
things that differ between two genuine payments — the amount and the payer name — occupy
a few hundred pixels that vanish completely on downscale.

Measured on simulated GPay success screens:

| Hash grid | Bits | Re-compressed replay<br>*(should be LOW)* | Two different genuine payments<br>*(should be HIGH)* |
|---|---|---|---|
| 16×16 | 256 | 29 bits differ | **3 bits differ** |
| 32×32 | 1024 | 44 bits differ | **1 bit differs** |
| 64×64 | 4096 | 212 bits differ | **5 bits differ** |

**The signal is inverted.** A genuine replay differs *more* than two unrelated payments
do, because WhatsApp re-compresses every image it forwards. There is no usable threshold
at any resolution — set it loose enough to catch real fraud and it flags every honest
customer.

### Design response

Anchor detection on data that survives compression:

- **The UTR reference number** (R1) — unique per transaction, survives re-cropping and
  re-screenshotting, and has a checkable 12-digit NPCI format
- **The exact file bytes** (R2) — a 128-bit FNV-1a hash over the raw buffer. Exact match
  only, so it has **zero false positives by construction**. It catches a literally
  forwarded file and nothing else.

This is the single most important architectural decision in the project.

---

## Architecture

```
Customer sends UPI screenshot on WhatsApp
             │
             ▼
  1. FILE FINGERPRINT      → 128-bit FNV-1a over raw bytes
                             exact-match only, catches forwarded copies
             │
             ▼
  2. FIELD EXTRACTION      → amount, UTR, payee VPA, timestamp
                             (OCR — simulated in this prototype)
             │
             ▼
  3. RULE ENGINE           → 8 weighted rules → risk score 0–100
             │
             ▼
  4. GATEWAY CROSS-CHECK   → match UTR against bank settlement
             │
             ▼
  GREEN 0-24  │  YELLOW 25-49  │  RED 50-100
```

---

## Running it

```bash
git clone https://github.com/printshop39-byte/fraudshield-upi.git
```

Then open `fraud-detection-prototype.html` in any modern browser. That's the whole setup.

No npm, no Python, no server. The page works fully offline — webfonts are loaded from
Google Fonts when a connection is available and fall back cleanly to system faces when
it isn't.

### Demo walkthrough

1. **Dashboard** — screened volume, fraud blocked, amount protected, coverage rate
2. **Verify → "Genuine payment"** — score 0, Green
3. **Verify → "Screenshot replay"** — score 90, Red (UTR already used)
4. **Verify → "Wrong UPI ID"** — score 85, Red (money went to another VPA)
5. **Verify → "Edited amount"** — score 95, Red (₹12,500 claimed vs ₹1,250 due, 3 days old)
6. Turn **"Payment gateway connected"** off and re-run the genuine case — Green becomes
   Yellow, demonstrating Flow A vs Flow B
7. Upload any image **twice** — the second submission is caught as an exact-file duplicate

---

## Prototype scope and honest limitations

This is a **prototype**, and the following are deliberately out of scope:

- **OCR is simulated.** Extracted fields are presented as editable inputs rather than read
  from the image. Production OCR on WhatsApp-compressed images is a real accuracy problem
  and would need its own evaluation.
- **No real bank integration.** The gateway cross-check is modelled as a toggle. Real
  verification needs a PSP webhook, bank credit SMS parsing, or the RBI Account
  Aggregator framework.
- **In-memory ledger.** State resets on page reload — there is no database.
- **Not a fraud accusation system.** Output language is deliberately *"could not verify"*,
  never *"this person is a fraudster"*. Telling an agent a customer is a fraudster and
  being wrong is a real legal exposure, so the copy never crosses that line.

---

## Where this goes next

- Bank credit **SMS parsing** on the agent's phone — the highest-value unlock, since most
  small agents will never have a payment gateway integration
- **Cross-tenant blocklist** of hashes and UTRs (irreversible, no PII) to catch the
  serial fraudster who reuses one screenshot across twenty different vendors
- **Coverage optimisation** — the share of screenings returning a definitive Green or Red
  rather than Yellow. A system that answers "needs review" 70% of the time is not useful
  regardless of its accuracy on the rest.
- Eliminate the screenshot entirely: **dynamic UPI collect requests** with a unique
  per-invoice reference, which makes this class of fraud structurally impossible

---

## Tech

Vanilla HTML, CSS, and JavaScript in one file. No frameworks, no dependencies, no build
step. Canvas is used for the file-hash experiments; everything else is plain DOM.

Type: Bricolage Grotesque (display), Public Sans (body), IBM Plex Mono (data),
Noto Sans Devanagari (Marathi).
