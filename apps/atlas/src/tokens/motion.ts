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
