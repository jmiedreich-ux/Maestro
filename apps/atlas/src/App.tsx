import { useEffect, useState } from "react";
import DesktopShell from "./shell/DesktopShell";
import MobileShell from "./shell/MobileShell";

/**
 * The real breakpoint from `Atlas Explorations.dc.html`'s own
 * `renderVals()`: `mobile = s.w < 880`. `DesktopShell.module.css`'s own
 * `.body` media query uses a different value (`900px`) for its own
 * internal nav-collapse behavior — a separate, narrower concern from
 * which top-level shell mounts, not a mismatch to reconcile here.
 */
const MOBILE_BREAKPOINT_PX = 880;

function isMobileWidth(): boolean {
  return window.innerWidth < MOBILE_BREAKPOINT_PX;
}

export function App() {
  const [isMobile, setIsMobile] = useState(isMobileWidth);

  useEffect(() => {
    function handleResize() {
      setIsMobile(isMobileWidth());
    }
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return isMobile ? <MobileShell /> : <DesktopShell />;
}

export default App;
