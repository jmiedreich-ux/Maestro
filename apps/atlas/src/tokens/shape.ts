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
