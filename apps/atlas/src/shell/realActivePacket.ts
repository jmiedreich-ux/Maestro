/**
 * M3 real-data wiring — a genuine, disclosed stopgap: there is no real
 * "list active packets, pick the current one" mechanism/API yet (that's
 * a separate, real feature this doesn't build), so the one currently
 * in-progress real packet is named directly. When a real packet
 * selector exists, replace this with its own real current-selection
 * state instead. Shared by DesktopShell and MobileShell/ChatTab so both
 * surfaces point at the same real packet.
 */
export const REAL_ACTIVE_PACKET_ID = "packet-foundry-cg-m4-20-v2";
