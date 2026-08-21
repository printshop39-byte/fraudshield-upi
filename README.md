# FraudShield — UPI Fraud Detection

A working prototype that screens the three things Indian UPI fraud actually arrives as: a
**scam message**, a **UPI ID or QR code**, and a **payment screenshot**. Built as a single
self-contained HTML file — no build step, no server, no `package.json`. Everything you paste
or upload is read in the browser and is **never sent anywhere**.

> ### ▶ [Live demo — printshop39-byte.github.io/fraudshield-upi](https://printshop39-byte.github.io/fraudshield-upi/)
>
> Nothing to install. Or clone the repo and open `index.html` directly — it runs
> the same offline.

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

## Three checks in one place

| Module | Answers |
|---|---|
| **Message Scanner** | Is this WhatsApp or SMS a scam? 15 heuristics for Indian fraud in **English, Marathi and Hindi** — UPI-PIN-to-receive, APK links, remote-access apps, KYC and reward bait, task-job scams, spoofed sender IDs. Devanagari and Roman-script Marathi both covered |
| **UPI ID & QR Check** | Is this UPI ID safe to pay? Validates the handle against the NPCI list, flags impersonation wording, and parses `upi://` QR text for pre-filled amounts |
| **Verify Payment** | Is this payment screenshot genuine? 12 weighted rules over OCR-read fields |

Every module scores 0–100, explains each finding in plain language, and ends with what to do next. Nothing is uploaded — all of it runs in the browser.

**English / मराठी throughout.** A switcher in the header translates navigation, headings, the safety modules and the quiz, including the ten quiz messages themselves. A sticky reminder sits above every page: *सुवर्ण नियम: पैसे मिळवण्यासाठी UPI PIN ची गरज नसते!*

---

## What the payment verifier does

Feed it a payment claim — a screenshot plus the extracted fields — and it returns an
**explainable risk verdict** in under a second.

- **Reads the screenshot** — amount, reference, payee UPI ID, payer name, mobile and status
  are pulled out by OCR running entirely in your browser, then marked for you to check
- **Risk score 0–100** from a twelve-rule weighted engine
- **Green / Yellow / Red** verdict with an explicit threshold and a recommended action
- **Per-rule breakdown** — every check states why it passed or failed
- **Payment direction** — tells you when a screenshot is a payment you *sent*, or when your
  UPI ID is entered with the wrong bank handle
- **Transaction ledger** with severity striping and verdict filters
- **Fraud analytics** — which rule is catching what, and repeat-offender tracking

Eight one-click demo cases are built in, and you can upload a real screenshot or edit any
field to drive the engine yourself. **Set your own merchant UPI ID first** — every payee is
compared against it.

### Verdict thresholds

| Score | Verdict | Action |
|---|---|---|
| 0 – 24 | 🟢 **Green** | Auto-accept |
| 25 – 49 | 🟡 **Yellow** | Manual review |
| 50 – 100 | 🔴 **Red** | Block + alert |

---

## The rule engine

Twelve weighted rules. A rule fires when its **fraud condition** is present, and its weight
is added to the risk score.

| ID | Rule | Detects | Weight |
|---|---|---|---|
| R10 | Transaction status | Pending or failed payment shown as proof | 65 |
| R1 | UTR reuse detection | Same reference number claimed twice | 60 |
| R2 | Exact file duplicate | Identical image file forwarded again | 55 |
| R3 | Payee VPA verification | Money sent to a different UPI ID | 55 |
| R4 | Amount integrity check | Edited or mismatched amount | 45 |
| R9 | Payer identity consistency | Mobile number reused under a different name | 40 |
| R11 | Duplicate claim window | Same payer claiming the same amount twice | 35 |
| R5 | UTR format validation | Fabricated reference number | 30 |
| R8 | Bank settlement match | No real money received | 30 |
| R6 | Timestamp freshness | Old transaction reused as new | 20 |
| R12 | Receipt completeness | Cropped or fabricated receipt | 20 |
| R7 | Payer velocity check | Unusual submission frequency | 15 |

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
  2. FIELD EXTRACTION      → amount, UTR, payee + payer VPA, mobile,
                             payer name, status — Tesseract.js in-browser
             │
             ▼
  3. RULE ENGINE           → 12 weighted rules → risk score 0–100
             │
             ▼
  4. GATEWAY CROSS-CHECK   → match UTR against bank settlement
             │
             ▼
  GREEN 0-24  │  YELLOW 25-49  │  RED 50-100
```

---

## Running it

Open the **[live demo](https://printshop39-byte.github.io/fraudshield-upi/)** — nothing to
install.

To run it locally instead:

```bash
git clone https://github.com/printshop39-byte/fraudshield-upi.git
```

Then open `index.html` in any modern browser. That's the whole setup.

No npm, no Python, no server. The page itself works offline — webfonts fall back to system
faces without a connection. **OCR needs the internet the first time**, to fetch Tesseract.js
from a CDN; without it the form drops to manual entry and says so, and every rule except the
OCR-dependent ones still applies.

### Demo walkthrough

1. **Dashboard** — screened volume, fraud blocked, amount protected, coverage rate
2. **Verify → "Genuine payment"** — score 0, Verified — Low Risk
3. **"Screenshot replay"** — 90, Red (UTR already used)
4. **"Wrong UPI ID"** — 85, Red (money went to another VPA)
5. **"Edited amount"** — 95, Red (₹12,500 claimed vs ₹1,250 due, 3 days old)
6. **"Payer identity mismatch"** — 70, Red (known mobile number, new name)
7. **"Pending payment"** — 95, Red (never settled, shown as paid)
8. **"Double claim"** — 80, Red (same payer, same amount, fresh reference)
9. Turn **"Payment gateway connected"** off and re-run the genuine case — Green becomes
   Yellow, demonstrating Flow A vs Flow B
10. Upload any image **twice** — the second is caught as an exact-file duplicate
11. Upload a real screenshot and open **"What the screenshot reader saw"** to see the OCR
    output the fields were filled from

---

## Prototype scope and honest limitations

This is a **prototype**, and the following are deliberately out of scope:

- **OCR accuracy is not guaranteed.** Tesseract.js reads the screenshot in the browser and
  fills the fields, but every value is marked for checking rather than trusted, and the raw
  text it read is shown so you can see what it actually saw. Amounts are the field it misses
  most often, since a stylised rupee glyph defeats the parser. Accuracy on WhatsApp-
  recompressed images is meaningfully worse than on a direct screenshot.
- **First OCR use downloads about 14 MB** of library, WebAssembly and language data from a
  CDN. It is cached afterwards and never fetched unless you upload an image — but on mobile
  data it is a real cost.
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

Vanilla HTML, CSS, and JavaScript in one file. No framework, no build step, no
`package.json`. One runtime dependency — Tesseract.js, fetched from a CDN only when an image
is uploaded, so the page still loads in a handful of requests and still works with no
network. Canvas is used for the file-hash experiments; everything else is plain DOM.

Type: Bricolage Grotesque (display), Public Sans (body), IBM Plex Mono (data),
Noto Sans Devanagari (Marathi).
