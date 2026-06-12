# Data dictionary

## Source fields (SBA 7(a) FOIA CSV)

The raw files carry 43 columns; this project reads the subset below
(`src/config.py:RAW_COLUMNS`). Field names are the SBA originals.

| Raw field | Meaning | Used for |
|---|---|---|
| `program` | SBA program (here always ` 7A`) | provenance |
| `borrname` | Borrower name | (not analysed; identity only) |
| `borrstate` | Borrower state | state concentration |
| `bankname` | Originating lender | lender concentration |
| `grossapproval` | Gross loan amount approved ($) | exposure, size bands, $ rates |
| `sbaguaranteedapproval` | SBA-guaranteed portion ($) | reference |
| `approvaldate` | Approval date (MM/DD/YYYY) | vintage, loan age |
| `approvalfy` | Approval fiscal year | vintage cohort |
| `terminmonths` | Loan term (months) | reference |
| `naicscode` | 6-digit industry code | → 2-digit NAICS sector |
| `naicsdescription` | Industry description | reference |
| `projectstate` | Project location state | reference |
| `businesstype` | Corporation / Individual / Partnership | reference |
| `jobssupported` | Jobs reported supported | reference |
| `loanstatus` | Final loan status code | default flag, stage proxy |
| `paidinfulldate` | Paid-in-full date | as-of inference, seasoning |
| `chargeoffdate` | Charge-off date | loan age at charge-off, cohort curves |
| `grosschargeoffamount` | Amount charged off ($) | $ charge-off rate |

## LoanStatus codes (as they appear, incl. embedded spaces)

| Code | Plain English | Treatment |
|---|---|---|
| `P I F` | Paid in full | Performing |
| `CURR` | Current | Performing |
| `CHGOFF` | **Charged off** | **Default** |
| `CANCLD` | Cancelled (never funded) | **Excluded** from universe |
| `COMMIT` | Committed (never funded) | **Excluded** from universe |
| `PURCH(NOT C/O)` | Guaranty purchased, not charged off | Performing (non-default) |
| `LIQUID` | In liquidation | Non-default (no charge-off booked) |
| `CLSLN` | Closed loan | Non-default |
| `DELINQ` / `PSTDUE` / `DEFERD` | Delinquent / past due / deferred | Non-default |

> Only `CHGOFF` counts as default per the build spec. `CANCLD`/`COMMIT` never
> funded and are dropped so they don't distort exposure or rates.

## Derived fields (base table — `src/base_table.py`)

| Field | Definition |
|---|---|
| `vintage` | `approvalfy` — the approval-year cohort |
| `is_default` | `loanstatus` in `universe.default_statuses` (i.e. `CHGOFF`) |
| `size_band` | `grossapproval` bucketed by `config.yaml:size_bands` |
| `naics_sector_code` | First 2 digits of `naicscode` |
| `naics_sector` | 2-digit code mapped to a NAICS sector name |
| `months_to_chargeoff` | `(chargeoffdate − approvaldate)` in months, defaults only |
| `fully_seasoned` | `vintage <= universe.fully_seasoned_max_fy` |
| `status_label` | Plain-English label for `loanstatus` |
