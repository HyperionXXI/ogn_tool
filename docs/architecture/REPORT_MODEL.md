# Report model

`report.json` is the stable analytical summary of an analysis run.

Constraints:

- must remain small (< 100 KB)
- must contain only analytical summaries
- heavy payloads must not be embedded
- large artifacts must be stored under `artifacts/`

Schema versioning:

The structure is versioned via:

`report_metadata.report_schema_version`
