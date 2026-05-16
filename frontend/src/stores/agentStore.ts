import { create } from "zustand";
import type { AgentRunResult } from "@/lib/api";

type AgentStore = {
  latestResult: AgentRunResult | null;
  setLatestResult: (result: AgentRunResult) => void;
  clearLatestResult: () => void;
};

export const useAgentStore = create<AgentStore>((set) => ({
  latestResult: null,
  setLatestResult: (result) => set({ latestResult: result }),
  clearLatestResult: () => set({ latestResult: null })
}));
