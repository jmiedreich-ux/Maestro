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
