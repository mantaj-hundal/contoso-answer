# Optional presentation authoring source

`build_deck.mjs` and `evidence.json` are the source used for the delivered deck.
It uses Artifact Tool 2.8.119 and the original presentation skill's finalization
helpers, not the Python analysis dependencies. Set `PRESENTATIONS_SKILL_DIR`,
`RUNTIME_PYTHON` and `RUNTIME_NODE_MODULES` to that authoring runtime and make
`@oai/artifact-tool` resolvable to Node. Output paths in this copy resolve under
`presentation/`. Use a new output filename to avoid the finalizer's overwrite check.
The original private authoring runtime is not redistributed. This source is
included for completeness; the analysis and figures do not depend on it.
