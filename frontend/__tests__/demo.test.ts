import { describe, expect, it } from "vitest";
import { demoAnalysis, demoMeals, sumMealCalories } from "../src/lib/demo";

describe("demo dashboard data", () => {
  it("keeps meal calorie totals aligned with the dashboard snapshot", () => {
    expect(sumMealCalories(demoMeals)).toBe(demoAnalysis.totals.calories);
  });
});
