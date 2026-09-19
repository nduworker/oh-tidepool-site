# Published data

CI publishes the optional app weather snapshot as `daily-conditions.json`.
The file must conform to the private app repository's documented v1 daily
conditions contract, including non-empty `revision`, `generated_at`,
`published_at`, and `expires_at` values. Publish the complete set of locations
in one commit only after validation; never replace the last good file with a
partial provider result.
