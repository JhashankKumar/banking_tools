/** Browser-side configuration. The browser only ever talks to same-origin routes. */
export const API_BASE = "/api";
export const AUTH_BASE = "/auth";
export const REQUEST_TIMEOUT_MS = 20_000;
/** A copilot question: the API's 90 s run deadline plus one 30 s model call, with margin. */
export const COPILOT_TIMEOUT_MS = 150_000;
/** Rows per page for every paginated list. */
export const LIST_PAGE_SIZE = 50;
