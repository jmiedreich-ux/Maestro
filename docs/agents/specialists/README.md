# Project Specialist Agent Overlays

Specialist overlays live with the joined project whenever they contain project architecture, source paths, or product rules. Maestro keeps these reference examples and the contract shape so that each project can bind its own roles without making Maestro project-specific.

Each overlay must declare:

- authority and read-first paths;
- owned concepts, invariants, and allowed/forbidden paths;
- queue entry conditions and expected integration dependencies;
- valid parallelism and required locks;
- routing constraints and evidence;
- escalation conditions;
- explicit relationship to the common Coding Agent SOP.

Start new project-specific roles from [specialist-overlay-template.md](specialist-overlay-template.md). The examples below use VennueSign terminology solely to show the expected level of specificity. Their live authority remains in VennueSign's project records.

| Example overlay | Purpose |
|---|---|
| [content-platform-agent.md](content-platform-agent.md) | Content model, records, providers, publication contracts |
| [theme-studio-agent.md](theme-studio-agent.md) | Reusable theme authoring and versioned handoff |
| [screens-agent.md](screens-agent.md) | Screen composition consuming published content/theme contracts |
| [display-runtime-agent.md](display-runtime-agent.md) | Player/rendering/delivery behavior |
