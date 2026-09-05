# M2 Wave B — Design Tokens Module — Candidate 01

**Slice ID:** `MB-SLICE-M2-B2-DESIGN-TOKENS-01`
**Status:** `Frozen — Pending Implementation`. Full Decision Fidelity review found 1 blocking finding (`performanceSeriesColors` sourced from outside the Design Tokens section, mislabeled); one targeted planning correction resolved it and was approved by targeted verification. No further planning correction is available for this slice.
**Base:** `d3275dc` (`origin/master`)

## Scope, deliberately minimal

Wave B2 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md): the design
tokens module. Adds four new TypeScript modules under
`apps/atlas/src/tokens/` (`colors.ts`, `typography.ts`, `motion.ts`,
`shape.ts`, plus an `index.ts` barrel) transcribing the Owner-supplied
design handoff's token values, and nothing else. **No consumer imports
these modules yet** — B3 (desktop shell) is the first slice that renders
anything with them. This slice adds zero visual output, zero new route,
zero CSS file, and no Google Fonts loading (loading the actual font files
is a rendering concern for whichever slice first needs text to render in
those fonts — B3).

Source of truth is exactly one file:
`design_handoff_atlas/README.md`'s "Design Tokens" section (`### Type`,
`### Color`, `### Shape & spacing`, all three H3s under the `## Design
Tokens` H2 — corrected heading levels; a prior draft of this paragraph
mislabeled `### Type` as an H2, caught by Decision Fidelity review), as
supplied by the Owner in the uploaded design-handoff zip earlier this
session and already the named authority for the M2 roadmap's Wave B-D
decomposition. Every value in the four token modules below is
transcribed verbatim from that section — quoted alongside each file so a
reviewer can check transcription accuracy line-by-line without needing
the original file open.

**What this token layer deliberately does NOT capture:** the README's
per-screen padding/sizing prose (e.g. "Thread: rows on a `36px
minmax(0,1fr)` grid... `34px` side padding") describes one specific
screen's layout, not a reusable cross-cutting primitive — encoding every
such number into this shared module would be guessing which are
"tokens" and which are one screen's own layout math, a judgment call
that belongs to whichever later slice actually builds that screen and
can check its own rendered output against the reference `.dc.html` file.
This slice captures only the values the README itself presents, **within
the Design Tokens section**, as general design-system primitives: the
Type and Color tables in full; from "Shape & spacing," the *radii*,
*gutters*, *card padding ranges*, *touch-target minimums*, the two named
animations, and the "Focus/hover" bullet's four colors (three tinted
borders plus the lightened-card ground — colors, so they live in
`colors.ts` even though the bullet they come from is physically inside
the Shape & spacing subsection). It deliberately excludes the same
paragraph's box-shadow/elevation values (the timeline-dot halo
specification) — those describe one specific component's effect, not a
reusable primitive, the same reasoning that excludes per-screen grid
columns.

**Corrected — blocking finding from Decision Fidelity review:** an
earlier draft of this slice also defined `performanceSeriesColors`, four
hex values quoted from the Performance screen's own prose (`## Desktop
screens > ### 2. Performance > **M1-A breakdown card**`), not from the
Design Tokens section at all — a real violation of this slice's own
sourcing rule, and its "Source quote" block was written in a way that
made the citation look like it came from the Color table. That constant
has been removed entirely from this slice. It belongs to whichever later
slice actually builds the Performance view (Wave E1-E3 per the roadmap),
which can transcribe it directly from the screen's own prose at the point
it is actually needed, exactly like every other per-screen value this
slice already declines to capture.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-B2-DESIGN-TOKENS-01` |
| `phase` | `PendingImplementation` |
| `current_actor` | `none` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:d3275dc","git:full-planning-review-head:64a98dede86e9eb490a131707ce6ea5dc1a0c669","review:decision-fidelity:request-changes:1-blocking-finding","git:corrected-planning-head:f35c2d2da4b429af876a0e60ce0bfb42e5bf37e6","review:targeted-decision-fidelity-verification:approve"]` |

## Exact file contents

Source quote (README, "### Color" table in full), for direct comparison
against `colors.ts` below:

> | Token | Hex | Use |
> | Nav ground | `#2A2233` | ... | Nav text | `#CFC6D6` | nav body; active
> item `#FFFFFF`, inactive item `#B7ADC1`, dim `#8E8299` | Nav active bg |
> `rgba(255,255,255,.13)` | selected nav row; hover `rgba(255,255,255,.06)`
> | Ink | `#221C29` | Ink secondary | `#6C6376` | Ink muted | `#8E8299` |
> Ink faint | `#A79BB4` | Accent | `#5B34E8` | ...hover/darker `#4A28CC`,
> deepest `#3F1FC0` | Accent light | `#8C6BFF` / `#A78BFF` | Accent wash |
> `#EBE4FF` / `#E7E1FB` / `#EFEBFB` / `#F0ECFB` / `#F4F0FE` | Page bg
> (desktop) | `#FCFBFD` | Page bg (mobile) | `#F7F5FA` | Surface |
> `#FFFFFF` | Border | `#E7E1EE`; lighter dividers `#EEEAF2`, `#F3F0F6`,
> `#F0ECF5` | Border strong | `#D6CFE4` / `#DAD2EC` | Dashed border |
> `#DCD5E4` / `#D6CFE0` / `#B9AFC4` | Success | `#2E9B72` text `#1F6B4E`
> wash `#E4F6EE` | Warning/decision | `#E0A32E` text `#8A5A08` wash
> `#FEF9F0` border `#F1DEBE` chip `#FDF1DC` | Danger | `#C4564A` text
> `#A63F36` wash `#FEF7F6` border `#EFC9C4` divider `#F6E2DF` | Review
> (orange) | `#D08A63` text `#A9522B` wash `#FBEDE7` | Neutral chip |
> `#F2EEF8` text `#4A4155`/`#6C6376` | Segmented track | `#EDE9F3` /
> `#F4F1F8` / `#F2EFF7`; selected pill `#FFFFFF` |

**Second, separate source quote — corrected, per Decision Fidelity
review: this is from `### Shape & spacing`, not `### Color`**, quoted
here (not with the block above) because it is the one place `colors.ts`
draws from outside the Color table, per the "Scope" section's now-explicit
carve-out:

> Focus/hover: cards lighten to `#FCFBFD` or gain a tinted border
> (`#E0C79A` amber, `#C9BEDC` neutral, `#EBBDB7` red).

`apps/atlas/src/tokens/colors.ts` (new):

```ts
/**
 * Color tokens, transcribed verbatim from
 * design_handoff_atlas/README.md's "### Color" table and "Semantic
 * rule" paragraph, plus the four `focusHover*` values below, which come
 * from the "Focus/hover" bullet in the neighboring "### Shape &
 * spacing" section (they are colors, so they live here regardless of
 * which subsection of the README states them). Do not rename, round, or
 * "clean up" a value without re-checking that file — it is the source
 * of truth, not this one.
 */

export const colors = {
  navGround: "#2A2233",
  navText: "#CFC6D6",
  navTextActive: "#FFFFFF",
  navTextInactive: "#B7ADC1",
  navTextDim: "#8E8299",
  navActiveBg: "rgba(255,255,255,.13)",
  navHoverBg: "rgba(255,255,255,.06)",

  ink: "#221C29",
  inkSecondary: "#6C6376",
  inkMuted: "#8E8299",
  inkFaint: "#A79BB4",

  accent: "#5B34E8",
  accentHover: "#4A28CC",
  accentDeepest: "#3F1FC0",
  accentLight: "#8C6BFF",
  accentLiveDot: "#A78BFF",
  accentWash: ["#EBE4FF", "#E7E1FB", "#EFEBFB", "#F0ECFB", "#F4F0FE"] as const,

  pageBgDesktop: "#FCFBFD",
  pageBgMobile: "#F7F5FA",
  surface: "#FFFFFF",

  border: "#E7E1EE",
  borderDivider: ["#EEEAF2", "#F3F0F6", "#F0ECF5"] as const,
  borderStrong: ["#D6CFE4", "#DAD2EC"] as const,
  borderDashed: ["#DCD5E4", "#D6CFE0", "#B9AFC4"] as const,

  success: "#2E9B72",
  successText: "#1F6B4E",
  successWash: "#E4F6EE",

  warning: "#E0A32E",
  warningText: "#8A5A08",
  warningWash: "#FEF9F0",
  warningBorder: "#F1DEBE",
  warningChip: "#FDF1DC",

  danger: "#C4564A",
  dangerText: "#A63F36",
  dangerWash: "#FEF7F6",
  dangerBorder: "#EFC9C4",
  dangerDivider: "#F6E2DF",

  review: "#D08A63",
  reviewText: "#A9522B",
  reviewWash: "#FBEDE7",

  neutralChip: "#F2EEF8",
  neutralChipText: "#4A4155",
  neutralChipTextAlt: "#6C6376",

  segmentedTrack: ["#EDE9F3", "#F4F1F8", "#F2EFF7"] as const,
  segmentedSelected: "#FFFFFF",

  focusHoverCard: "#FCFBFD",
  focusHoverBorderAmber: "#E0C79A",
  focusHoverBorderNeutral: "#C9BEDC",
  focusHoverBorderRed: "#EBBDB7",
} as const;

/**
 * Semantic color rule (README, verbatim): amber = a human is needed;
 * purple = an agent is deciding/recording; red = something broke; green
 * = verified/met; grey = idle or unavailable. Never use green for
 * "billed" or amber for "error" — amber specifically means waiting on a
 * person or an estimate. This constant exists so a lint/review pass can
 * grep for it; it is not consumed programmatically by this slice.
 */
export const SEMANTIC_COLOR_RULE =
  "amber=human-needed purple=agent-deciding red=broken green=verified grey=idle-or-unavailable" as const;
```

Source quote (README, "### Type"), for direct comparison against
`typography.ts` below:

> Display / headings: `Bricolage Grotesque` 600, letter-spacing −0.02em to
> −0.03em, line-height 1.15–1.3. Body / UI: `Public Sans` 400/600/700,
> default body size 13.5–14.5px. Numeric/identifiers/labels: `IBM Plex
> Mono` 500/600. Uppercase eyebrow label: `600 10.5px IBM Plex Mono`,
> `letter-spacing: .11em`, `text-transform: uppercase`. Mobile variant:
> `10px`/`9.5px`, `letter-spacing: .12em`. Type scale actually used: 30,
> 25, 23/21, 19/17.5, 16, 15.5/15/14.5, 13.5/13, 12.5/12,
> 11.5/11/10.5/10/9.5.

`apps/atlas/src/tokens/typography.ts` (new):

```ts
export const fontFamily = {
  display: '"Bricolage Grotesque", ui-sans-serif, system-ui, sans-serif',
  body: '"Public Sans", ui-sans-serif, system-ui, sans-serif',
  mono: '"IBM Plex Mono", ui-monospace, SFMono-Regular, monospace',
} as const;

export const fontWeight = {
  displayHeading: 600,
  bodyRegular: 400,
  bodySemibold: 600,
  bodyBold: 700,
  monoMedium: 500,
  monoSemibold: 600,
} as const;

/** Display/heading tracking and leading range (README, verbatim). */
export const displayHeading = {
  letterSpacingEm: { min: -0.03, max: -0.02 },
  lineHeight: { min: 1.15, max: 1.3 },
} as const;

/** Default body text size range, in px (README, verbatim). */
export const bodyFontSizePx = { min: 13.5, max: 14.5 } as const;

/** Uppercase eyebrow label spec (README, verbatim). */
export const eyebrowLabel = {
  desktop: { fontWeight: 600, fontSizePx: 10.5, letterSpacingEm: 0.11 },
  mobile: { fontSizePx: [10, 9.5] as const, letterSpacingEm: 0.12 },
  textTransform: "uppercase",
} as const;

/**
 * The full type scale actually used across the design, in descending px
 * order (README, verbatim) — every size any screen uses, nothing more,
 * nothing rounded to a "nicer" scale.
 */
export const typeScalePx = [
  30, 25, 23, 21, 19, 17.5, 16, 15.5, 15, 14.5, 13.5, 13, 12.5, 12, 11.5, 11,
  10.5, 10, 9.5,
] as const;
```

Source quote (README, "### Shape & spacing" animations line), for direct
comparison against `motion.ts` below:

> Animations: `rise` (fade + 4px translateY, `.18–.22s ease-out`) on cards
> appearing; `sheet` (translateY 100%→0, `.24s cubic-bezier(.32,.72,0,1)`)
> on the mobile bottom sheet. Keep both; they are the only motion.

`apps/atlas/src/tokens/motion.ts` (new):

```ts
/**
 * The only two motions this design uses (README: "Keep both; they are
 * the only motion.").
 */
export const motion = {
  rise: {
    description: "fade + 4px translateY, on cards appearing",
    translateYPx: 4,
    durationS: { min: 0.18, max: 0.22 },
    easing: "ease-out",
  },
  sheet: {
    description: "translateY 100% -> 0, on the mobile bottom sheet",
    translateFromPercent: 100,
    translateToPercent: 0,
    durationS: 0.24,
    easing: "cubic-bezier(.32,.72,0,1)",
  },
} as const;
```

Source quote (README, "### Shape & spacing", radii/gutter/touch-target
lines only — the per-screen prose lines are deliberately not
transcribed, per "Scope" above), for direct comparison against
`shape.ts` below:

> Radii: desktop cards `14px`, buttons `8–10px`, chips/tags `6px`, pills
> `999px`, small marks `3–5px`. Mobile cards `18–22px`, buttons/sheet
> controls `14–15px`, sheet `26px 26px 0 0`, segmented pill `10px`.
> Desktop content gutter `34px`; card padding `12–17px`; header padding
> `16px 34px 14–15px`. Mobile gutter `18px`; card padding `13–18px`; tab
> bar `6px 8px 4px`. Mobile touch targets: every button `min-height: 46px`
> or greater (tab bar rows 50px, sheet buttons 50px, option rows 56px).
> Do not go below 44px. Card gaps: desktop `8–14px`; mobile `8–12px`.

`apps/atlas/src/tokens/shape.ts` (new):

```ts
/**
 * Corner radii (README, verbatim). A single number is an exact value; a
 * `{min,max}` object is the stated range — do not collapse a range to
 * one number here, a later screen-building slice picks the specific
 * value its own component needs and checks it against the reference
 * `.dc.html` file.
 */
export const radii = {
  desktopCardPx: 14,
  desktopButtonPx: { min: 8, max: 10 },
  chipPx: 6,
  pillPx: 999,
  smallMarkPx: { min: 3, max: 5 },
  mobileCardPx: { min: 18, max: 22 },
  mobileButtonPx: { min: 14, max: 15 },
  sheetPx: "26px 26px 0 0",
  segmentedPillPx: 10,
} as const;

export const spacing = {
  desktopContentGutterPx: 34,
  desktopCardPaddingPx: { min: 12, max: 17 },
  desktopHeaderPadding: "16px 34px 14–15px",
  mobileGutterPx: 18,
  mobileCardPaddingPx: { min: 13, max: 18 },
  mobileTabBarPadding: "6px 8px 4px",
  desktopCardGapPx: { min: 8, max: 14 },
  mobileCardGapPx: { min: 8, max: 12 },
} as const;

/**
 * Minimum interactive touch-target heights (README, verbatim). Never
 * below 44px.
 */
export const touchTargetPx = {
  minimum: 44,
  defaultMinimum: 46,
  tabBarRow: 50,
  sheetButton: 50,
  optionRow: 56,
} as const;
```

`apps/atlas/src/tokens/index.ts` (new):

```ts
export * from "./colors";
export * from "./typography";
export * from "./motion";
export * from "./shape";
```

## Guards and boundary

1. Every file above lives under `apps/atlas/src/tokens/`; no file outside
   that directory is created, modified, or deleted.
2. No new npm dependency — these are plain TypeScript object literals,
   nothing else.
3. No consumer of these modules is added by this slice (no import from
   `App.tsx`, `main.tsx`, or anywhere else) — verified by the exact file
   boundary check below.
4. No CSS file, no Google Fonts `<link>`/`@import`, no change to
   `index.html` — loading fonts is a rendering-slice concern (B3), not a
   token-definition concern.

## Boundary, proof, and M0-D12

Writable paths are exactly the five files listed above, all newly
created under `apps/atlas/src/tokens/`, plus one new test file,
`apps/atlas/src/tokens/tokens.test.ts`. No other path — including every
file B1 created — is touched.

The 5 named tests, in `apps/atlas/src/tokens/tokens.test.ts` (Vitest,
matching B1's existing `test`/`typecheck`/`lint`/`build` scripts — no new
npm script is needed):

1. `colors module matches the README transcription exactly` — one
   `expect(colors).toEqual({...})` against a literal object the test
   itself spells out (independently re-typed in the test file, not
   imported from `colors.ts`, so a copy-paste error in the source file
   cannot also be present in its own check) covering every key in both
   quoted sources above (the Color table and the Focus/hover bullet); a
   second assertion for `SEMANTIC_COLOR_RULE`. (No assertion for
   `performanceSeriesColors` — that export no longer exists in this
   slice, per the corrected Scope section above.)
2. `typography module matches the README transcription exactly` — the
   same `toEqual`-against-an-independently-typed-literal pattern for
   `fontFamily`, `fontWeight`, `displayHeading`, `bodyFontSizePx`,
   `eyebrowLabel`, and `typeScalePx` (asserting the exact 19-element
   array, in the exact descending order quoted above).
3. `motion module matches the README transcription exactly` — same
   pattern for `motion.rise` and `motion.sheet`.
4. `shape module matches the README transcription exactly` — same
   pattern for `radii`, `spacing`, and `touchTargetPx`.
5. `no file outside src/tokens imports from src/tokens` — **corrected,
   non-blocking finding from Decision Fidelity review: the original
   `../..`-relative mechanism didn't resolve to the right directory from
   a Vitest process's actual working directory.** The exact, working
   mechanism: from within `tokens.test.ts`, compute the scan root as
   `path.resolve(import.meta.dirname, "..")` (i.e. `apps/atlas/src`,
   derived from the test file's own on-disk location, not from
   `process.cwd()`, which Vitest does not guarantee), then run
   ```
   execSync(
     `grep -rlE "from ['\\"](\\.\\./)*tokens(/|['\\"])" . --include="*.ts" --include="*.tsx" --exclude-dir=tokens`,
     { cwd: scanRoot },
   )
   ```
   and assert either the command exits non-zero (grep's own "no matches"
   exit code) or, if it exits zero, that its stdout is empty. This is a
   deliberately practical check, not exhaustive static analysis — per
   M0-D12's proportionality ceiling, it does not resolve TypeScript path
   aliases (none exist in `apps/atlas/tsconfig.json` today) and can in
   principle match a future unrelated file's comment containing the word
   "tokens"; both are accepted, documented limitations of a proportionate
   sanity check, not a claim of complete import-graph verification.

Run, from `apps/atlas/`: `npm run typecheck`, `npm run lint`, and
`npm test` (all must exit `0`, including the 5 new tests above alongside
B1's existing `App > renders the Atlas placeholder`); `npm run build`
must still succeed and still produce only the B1 placeholder output (the
tokens are not imported by anything the build bundles into `dist/`, so
`dist/` output is unaffected — confirmed by re-running B1's `check_04`
verbatim).

### M0-D12 bounded quality contract

1. **Protected outcome:** every numeric/hex/string design-token value
   this slice defines matches the README's own stated value exactly,
   with no rounding, renaming, or invented precision beyond what the
   README itself states (a stated range stays a range, not a guessed
   midpoint).
2. **Operating and threat model:** a trusted local single-user dev box;
   the only "threat" this slice's assurance model concerns itself with is
   human transcription error, checked by an independently-typed literal
   comparison in the test file (element 5 below).
3. **Explicit exclusions:** any per-screen layout number not presented by
   the README as a cross-cutting primitive (see "Scope" above); any CSS
   file, font loading, or visual rendering; any consumer of these
   modules (B3 and later); any design value not yet named anywhere in
   the README (nothing is invented ahead of need).
4. **Assurance level:** exact literal-value correctness, proportionate to
   a foundational, widely-reused token layer — a transcription error here
   would silently propagate into every later screen slice, so the
   assurance bar is "byte-exact against the quoted source," not "close
   enough."
5. **Acceptance proof:** the 5 named tests, `npm run typecheck`,
   `npm run lint`, and confirmation that `npm run build`'s output is
   unaffected, all passing.
6. **Implementation boundary:** exactly the six writable paths above
   (five token/barrel files plus the one test file); no new dependency;
   plain TypeScript object literals only, no runtime logic.
7. **Proportionality ceiling:** four small token modules and one barrel;
   no CSS-in-JS library, no design-token build pipeline (e.g. Style
   Dictionary), no generated CSS custom properties — this program has
   exactly one design source (the README) and exactly one consumer
   language (TypeScript) so far; a generation pipeline would be
   solving a problem this slice does not have yet.
8. **Stop and escalation rule:** if a later screen-building slice needs a
   value this module doesn't have, that slice adds it to the relevant
   token file (a small, additive, separately reviewed change) rather than
   guessing a value inline in a component — this module is not frozen
   against growth, only against inventing values the README doesn't
   state. A discovered proof/contract defect (a wrong transcribed value)
   against a frozen slice terminally returns that slice. One planning
   correction and one implementation correction are the maximum
   available.
