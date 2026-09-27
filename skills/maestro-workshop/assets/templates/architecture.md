# [Project name] — Architecture

| Field | Value |
|---|---|
| Document version | [Positive integer version] |

<!-- Replace prompts with system behavior. This document has no delivery assignments or milestone work. Add sections where needed to explain the system; each fact has one authoritative home. -->

## Purpose and boundaries

[Reference the overview's project purpose and scope. Describe only architecture-specific system boundaries here.]

## Components and responsibilities

| Component | Responsibility |
|---|---|
| [Component] | [What it does and where its responsibility ends] |

## Connections and data

| Connection | Mechanism | Information exchanged | Expected behavior |
|---|---|---|---|
| [Source to destination] | [Protocol or interface; identify unresolved choices] | [Inputs and outputs] | [How the components cooperate] |

| Record or information | Authoritative location | Read/write responsibility |
|---|---|---|
| [Record] | [Storage or source] | [Responsible component and relevant behavior] |

## Runtime and prerequisites

[Where and how the system runs, how required services become available, and the setup or access needed for the described journeys. Distinguish established choices from unresolved mechanisms.]

## Journeys and interactions

### [Journey subject]

**Starting condition:** [Required capability, setup, and state; references to dependency evidence.]

**Entry:** [Action or event that begins the journey.]

**Expected journey result:** [The usable outcome and its observable result.]

| Sequence | Interaction | Architecture reference |
|---|---|---|
| [Position] | [Plain interaction subject] | [Repository-relative path and heading fragment for its definition] |

#### [Interaction subject]

| Field | Description |
|---|---|
| Starting condition | [What must already be true] |
| Trigger | [Command, action, or event] |
| System behavior | [Components involved and their actions] |
| Expected result | [Visible result, state changes, recorded information, and relevant unchanged state] |
| Essential failure behavior | [What happens if completion is prevented; displayed failure or needed input] |

[Repeat for each associated interaction and journey. A shared interaction has one definition referenced by each journey that uses it.]

## Constraints and unresolved details

| Subject | Established constraint or unresolved detail | Effect on behavior |
|---|---|---|
| [Subject] | [Identify whether settled or provisional] | [Affected journey or interaction] |
