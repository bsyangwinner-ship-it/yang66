import { describe, expect, it } from "vitest";
import { formatCalories, formatPercent } from "../src/lib/format";

describe("format helpers", () => {
  it("formats calories with zh-CN thousands separators", () => {
    expect(formatCalories(1860.4)).toBe("1,860 kcal");
  });

  it("formats percentages", () => {
    expect(formatPercent(73.7)).toBe("74%");
  });
});
