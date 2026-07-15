import { describe, expect, it } from "vitest";

import { Counter } from "../src/Counter";

describe("Counter", () => {
  it("exports a component", () => {
    expect(Counter).toBeDefined();
  });
});
