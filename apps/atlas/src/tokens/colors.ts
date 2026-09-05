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
