import "@testing-library/jest-dom";

// ── localStorage polyfill for jsdom ──────────────────
// jsdom / Node may provide a partial localStorage. Replace with
// a full in-memory implementation so tests work reliably.
const store: Record<string, string> = {};
const localStorageMock: Storage = {
  get length() { return Object.keys(store).length; },
  key(index: number) { return Object.keys(store)[index] ?? null; },
  getItem(key: string) { return key in store ? store[key] : null; },
  setItem(key: string, value: string) { store[key] = String(value); },
  removeItem(key: string) { delete store[key]; },
  clear() { for (const k of Object.keys(store)) delete store[k]; },
};
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock, writable: true });

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
});
