import { create } from "zustand";

export type HealthGoal = "fat_loss" | "muscle_gain" | "maintenance" | "glucose_control" | "sleep_improvement";

type AppState = {
  currentGoal: HealthGoal;
  setCurrentGoal: (goal: HealthGoal) => void;
};

export const useAppStore = create<AppState>((set) => ({
  currentGoal: "fat_loss",
  setCurrentGoal: (goal) => set({ currentGoal: goal })
}));
