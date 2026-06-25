# Data dictionary

## Source fields (SBA 7(a) FOIA CSV)

The raw files carry 43 columns; this project reads the subset below
(`src/config.py:RAW_COLUMNS`). Field names are the SBA originals.

| Raw field | Meaning | Used for |
|---|---|---|
| `program` | SBA program (here always ` 7A`) | provenance |
| `subprogram` | 7(a) subprogram (the product within 7(a)) | → `product_type` family |
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
| `revolverstatus` | Revolving line (TRUE) vs term loan (FALSE) | → `loan_structure` |
| `collateralind` | Secured (TRUE) vs unsecured (FALSE) | → `collateral_status` |
| `loanstatus` | Final loan status code | default flag, stage proxy |
| `paidinfulldate` | Paid-in-full date | as-of inference, seasoning |
| `chargeoffdate` | Charge-off date | loan age at charge-off, cohort curves |
| `grosschargeoffamount` | Amount charged off ($) | $ charge-off rate |

## LoanStatus codes (as they appear, incl. embedded spaces)

| Code | Plain English | Treatment |
|---|---|---|
| `P I F` | Paid in full | Performing |
| `CURR` | Current | Performing |
| `CHGOFF` | **Charged off** | **Default** (realised) + non-performing |
| `CANCLD` | Cancelled (never funded) | **Excluded** from universe |
| `COMMIT` | Committed (never funded) | **Excluded** from universe |
| `PURCH(NOT C/O)` | Guaranty purchased, not charged off | **Non-performing** (problem exposure / Stage 2) — effective default |
| `LIQUID` | In liquidation | **Non-performing** (problem exposure / Stage 2) |
| `DELINQ` / `PSTDUE` | Delinquent / past due | **Non-performing** (problem exposure / Stage 2) |
| `DEFERD` | Deferred | Non-default (not in the problem-exposure set) |
| `CLSLN` | Closed loan | Performing (non-default) |
| `CURR` / `P I F` | Current / paid in full | Performing (non-default) |
| `SOLDNC` / `SOLDCO` | Sold (not / charged off) | Non-default; loan transferred (negligible volume) |

> `CHGOFF` is the realised **default**. The problem-exposure statuses
> (`DELINQ` / `PSTDUE` / `LIQUID` / `PURCH(NOT C/O)`) are **not** a realised
> charge-off, but together with `CHGOFF` they make the **non-performing (NPL)
> proxy** (`is_nonperforming`) — the closest stand-in for the APS 220 reference
> default (90+DPD/UTP). `CANCLD`/`COMMIT` never funded and are dropped so they
> don't distort exposure or rates.

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
| `product_type` | Use-of-proceeds facility type: trade/export → working-capital revolving → real-estate proxy (term >15y) → general SME term (`base_table.py`) |
| `loan_structure` | `revolverstatus` → Term loan / Revolving line of credit |
| `collateral_status` | `collateralind` → Secured / Unsecured (PPSR-equivalent) |
