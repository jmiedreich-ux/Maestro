import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "node_modules"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    rules: {
      // Explicit and defensive, not a fix for an active false positive:
      // typescript-eslint's own recommended config already disables
      // no-undef for .ts/.tsx files (TypeScript's checker already
      // catches undefined identifiers with full type information), so
      // this line currently changes nothing observable. It stays as a
      // literal statement of intent in case a future config change ever
      // reintroduces the rule for these files.
      "no-undef": "off",
    },
  },
);
