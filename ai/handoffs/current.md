# Current Maestro development state

- Scope: [ordered outcomes](../../docs/product/v1/outcomes.md).
- Status: every outcome is delivered except those whose criteria changed with the new process: the registration outcomes (blank Result rows in [the registration outcomes](../../docs/product/v1/outcomes/registration.md)) and one Execution row. Evidence is in each outcome document's Result column and the `passed/*` tags. The builder has stopped.
- In progress: moving Maestro onto the new process. The maestro-workshop skill now holds all process documents. Registration is being redesigned so the workshop does the thinking and the service checks documents against `registration-rules.json`. See [the registration process](../../skills/maestro-workshop/process/registration-process.md) and [the rules-file feature](../../docs/product/v1/features/registration-reads-rules-file.md).
- Done: the architecture's Registration section, the registration outcome and the role contracts now describe the new process.
- Next: the work still to do is in the feature plans in [features](../../docs/product/v1/features/): registration reads the rules file, the roadmap in the new format, removing the work-disposition choices, the architecture stage in the new process, and stronger outcome criteria.
