import { describe, expect, test } from "vitest";

import { colors, SEMANTIC_COLOR_RULE } from "./colors";
import {
  fontFamily,
  fontWeight,
  displayHeading,
  bodyFontSizePx,
  eyebrowLabel,
  typeScalePx,
} from "./typography";
import { motion } from "./motion";
import { radii, spacing, touchTargetPx } from "./shape";

describe("design tokens", () => {
  test("colors module matches the README transcription exactly", () => {
    expect(colors).toEqual({
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
      accentWash: ["#EBE4FF", "#E7E1FB", "#EFEBFB", "#F0ECFB", "#F4F0FE"],

      pageBgDesktop: "#FCFBFD",
      pageBgMobile: "#F7F5FA",
      surface: "#FFFFFF",

      border: "#E7E1EE",
      borderDivider: ["#EEEAF2", "#F3F0F6", "#F0ECF5"],
      borderStrong: ["#D6CFE4", "#DAD2EC"],
      borderDashed: ["#DCD5E4", "#D6CFE0", "#B9AFC4"],

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

      segmentedTrack: ["#EDE9F3", "#F4F1F8", "#F2EFF7"],
      segmentedSelected: "#FFFFFF",

      focusHoverCard: "#FCFBFD",
      focusHoverBorderAmber: "#E0C79A",
      focusHoverBorderNeutral: "#C9BEDC",
      focusHoverBorderRed: "#EBBDB7",
    });

    expect(SEMANTIC_COLOR_RULE).toEqual(
      "amber=human-needed purple=agent-deciding red=broken green=verified grey=idle-or-unavailable",
    );
  });

  test("typography module matches the README transcription exactly", () => {
    expect(fontFamily).toEqual({
      display: '"Bricolage Grotesque", ui-sans-serif, system-ui, sans-serif',
      body: '"Public Sans", ui-sans-serif, system-ui, sans-serif',
      mono: '"IBM Plex Mono", ui-monospace, SFMono-Regular, monospace',
    });

    expect(fontWeight).toEqual({
      displayHeading: 600,
      bodyRegular: 400,
      bodySemibold: 600,
      bodyBold: 700,
      monoMedium: 500,
      monoSemibold: 600,
    });

    expect(displayHeading).toEqual({
      letterSpacingEm: { min: -0.03, max: -0.02 },
      lineHeight: { min: 1.15, max: 1.3 },
    });

    expect(bodyFontSizePx).toEqual({ min: 13.5, max: 14.5 });

    expect(eyebrowLabel).toEqual({
      desktop: { fontWeight: 600, fontSizePx: 10.5, letterSpacingEm: 0.11 },
      mobile: { fontSizePx: [10, 9.5], letterSpacingEm: 0.12 },
      textTransform: "uppercase",
    });

    expect(typeScalePx).toEqual([
      30, 25, 23, 21, 19, 17.5, 16, 15.5, 15, 14.5, 13.5, 13, 12.5, 12, 11.5,
      11, 10.5, 10, 9.5,
    ]);
  });

  test("motion module matches the README transcription exactly", () => {
    expect(motion.rise).toEqual({
      description: "fade + 4px translateY, on cards appearing",
      translateYPx: 4,
      durationS: { min: 0.18, max: 0.22 },
      easing: "ease-out",
    });

    expect(motion.sheet).toEqual({
      description: "translateY 100% -> 0, on the mobile bottom sheet",
      translateFromPercent: 100,
      translateToPercent: 0,
      durationS: 0.24,
      easing: "cubic-bezier(.32,.72,0,1)",
    });
  });

  test("shape module matches the README transcription exactly", () => {
    expect(radii).toEqual({
      desktopCardPx: 14,
      desktopButtonPx: { min: 8, max: 10 },
      chipPx: 6,
      pillPx: 999,
      smallMarkPx: { min: 3, max: 5 },
      mobileCardPx: { min: 18, max: 22 },
      mobileButtonPx: { min: 14, max: 15 },
      sheetPx: "26px 26px 0 0",
      segmentedPillPx: 10,
    });

    expect(spacing).toEqual({
      desktopContentGutterPx: 34,
      desktopCardPaddingPx: { min: 12, max: 17 },
      desktopHeaderPadding: "16px 34px 14–15px",
      mobileGutterPx: 18,
      mobileCardPaddingPx: { min: 13, max: 18 },
      mobileTabBarPadding: "6px 8px 4px",
      desktopCardGapPx: { min: 8, max: 14 },
      mobileCardGapPx: { min: 8, max: 12 },
    });

    expect(touchTargetPx).toEqual({
      minimum: 44,
      defaultMinimum: 46,
      tabBarRow: 50,
      sheetButton: 50,
      optionRow: 56,
    });
  });
});
