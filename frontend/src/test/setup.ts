import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// O jsdom não implementa rolagem, mas a paginação chama scrollTo ao navegar.
Object.defineProperty(window, "scrollTo", { writable: true, value: () => {} });

afterEach(() => {
  cleanup();
});
