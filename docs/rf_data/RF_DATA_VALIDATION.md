STATUS: derived
REFERENCE: docs/core/ROADMAP_MASTER.md

This document is subordinate to docs/core/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# RF Data Validation

## 1. RF reception dataset

The `rf_receptions` dataset contains reception events derived from APRS traffic.

Fields (typical):

- receiver (station id)
- snr
- freq_offset
- bit_errors
- altitude
- ts_epoch

Data sources:

- APRS-IS packets with qA* receiver tags
- RF metrics parsed from packet body

Units:

- snr: dB
- freq_offset: kHz
- altitude: meters
- ts_epoch: seconds since epoch

## 2. RFObservation construction

RFObservation is built from RFEvent and station metadata:

- distance computation between receiver and aircraft
- bearing computation from receiver to aircraft
- altitude extraction from packet body or aircraft fields
- SNR normalization into a numeric dB value

## 3. Data quality risks

- missing altitude
- invalid coordinates
- SNR parsing errors
- duplicate receptions

## 4. Validation checks

- distance > 0
- latitude in [-90, 90]
- longitude in [-180, 180]
- snr is numeric

## 5. Impact on RF models

Empirical models and coverage inference depend on accurate observation data.
Invalid or biased inputs produce misleading RF metrics and coverage estimates.

