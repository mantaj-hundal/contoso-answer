# Submission packaging notes

The interview notebook and its computations were preserved. Packaging changes:

- Paths now resolve inside this extracted submission using `submission.json`,
  rather than requiring the analytics-workbench project or its context files.
- The notebook defaults to a generic Python kernel. The builder supports the
  `CONTOSO_KERNEL` override rather than requiring a personal registered kernel.
- The readable notebook template and `case_helpers/` functions/classes are
  included. `src/create_notebook.py` rebuilds and executes the template. Full
  and preparation-only script exports are generated directly from notebook code.
- This revision replaces long notebook implementation blocks with short named
  function calls. The original immutable submission is the numerical/audit
  equivalence reference. See `outputs/readability/equivalence.json`.
- Workstation-specific user paths in saved text outputs/manifests were redacted.
  Recorded dependency versions and numerical results were retained. Reruns record
  the executing interpreter and local paths for that run.
- Superseded development handoffs, internal skills, unrelated project records,
  installed runtimes, caches, junctions and private build artifacts are excluded.
- The supplied PowerPoint and slide evidence are included unchanged. Deck-authoring
  source is included separately for transparency, but requires the original
  Artifact Tool presentation-authoring runtime and its documented helper utilities.
  It is not required to reproduce the analysis, tables or figures.

The upstream source statement, license, pinned commit and raw CSV are preserved.
No cleaning rule, model specification, cohort definition, sample exclusion,
statistical result or recommendation was changed for packaging.
