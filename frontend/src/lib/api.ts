import { apiBaseUrl } from "./config";

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  user: { id: string; name: string; email: string };
};

export type HealthGoal = {
  id: string;
  goal_type: string;
  target_weight_kg?: number | null;
  target_calories?: number | null;
  target_protein_g?: number | null;
  start_date: string;
  end_date?: string | null;
  status: string;
};

export type HealthProfile = {
  age: number;
  gender: string;
  height_cm: number;
  weight_kg: number;
  sleep_hours: number;
  bedtime?: string | null;
  wake_time?: string | null;
  activity_level: string;
  exercise_frequency: number;
  dietary_preferences: string[];
  allergies: string[];
  budget_level?: string | null;
};

export type FitnessProfile = {
  exercise_level: string;
  weekly_frequency: number;
  preferred_exercise: string[];
  available_time_minutes: number;
  fitness_goal: string;
  contraindications: string[];
  is_sedentary: boolean;
};

export type FoodItem = {
  name: string;
  amount: number;
  unit: string;
  calories: number;
  protein_g: number;
  fat_g: number;
  carbs_g: number;
  fiber_g: number;
  sugar_g: number;
  sodium_mg: number;
};

export type Meal = {
  id: string;
  meal_date: string;
  meal_time?: string | null;
  meal_type: string;
  location?: string | null;
  source: string;
  note?: string | null;
  food_items: Array<FoodItem & { id?: string }>;
};

export type NutritionAnalysis = {
  id: string;
  analysis_date: string;
  score: number;
  totals: Record<string, number>;
  macro_balance: Record<string, number>;
  evidence: Record<string, unknown>;
  summary: string;
};

export type RiskAlert = {
  id: string;
  risk_type: string;
  severity: string;
  title: string;
  description: string;
  suggestion: string;
  status: string;
  evidence: Record<string, unknown>;
  created_at: string;
};

export type AgentSession = {
  id: string;
  user_id?: string;
  title?: string;
  goal_snapshot?: Record<string, unknown>;
  status?: string;
  created_at?: string;
  updated_at?: string;
};

export type AgentRun = {
  id: string;
  session_id?: string;
  graph_name?: string;
  state?: Record<string, unknown>;
  status: string;
  started_at?: string;
  finished_at?: string | null;
};

export type AgentMessage = {
  id?: string;
  session_id?: string;
  role?: string;
  content: string;
  metadata?: Record<string, unknown>;
  created_at?: string;
};

export type AgentToolCall = {
  id?: string;
  run_id?: string;
  tool_name: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  status: string;
  latency_ms: number;
  created_at?: string;
};

export type AgentRunResult = {
  session?: AgentSession;
  run: AgentRun;
  assistant_message: AgentMessage;
  state: {
    nutrition_analysis?: NutritionAnalysis;
    risks?: RiskAlert[];
    meal_plan?: Record<string, unknown>;
    exercise_recommendation?: Record<string, unknown>;
    intervention_plan?: Record<string, unknown>;
    rag_context?: Array<Record<string, unknown>>;
    tool_calls?: AgentToolCall[];
  };
};

export type AgentStreamEvent = {
  type: string;
  session?: AgentSession;
  run?: AgentRun;
  node?: string;
  label?: string;
  preview?: Record<string, unknown>;
  tool_call?: AgentToolCall;
  content?: string;
  result?: AgentRunResult;
  detail?: string;
};

export type Report = {
  id: string;
  report_type: string;
  period_start: string;
  period_end: string;
  title: string;
  status: string;
  summary: string;
  metrics: Record<string, unknown>;
  recommendations: Array<Record<string, unknown>>;
  export_object_key?: string | null;
  export_content?: string | null;
  generated_at?: string | null;
};

export type InterventionTask = {
  id: string;
  title: string;
  risk_type: string;
  task_type: string;
  priority: string;
  status: string;
  scheduled_for: string;
  due_date: string;
  description: string;
};

const TOKEN_KEY = "nutrition_agent_access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
}

export function saveToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

type RequestOptions = RequestInit & {
  auth?: boolean;
};

async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (options.auth !== false && token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers,
    cache: "no-store"
  });

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // Keep the HTTP status when the response is not JSON.
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function parseAgentSseBlock(block: string): AgentStreamEvent | null {
  const lines = block.trim().split(/\r?\n/);
  let type = "message";
  const dataLines: string[] = [];
  for (const line of lines) {
    if (line.startsWith("event:")) {
      type = line.slice("event:".length).trim();
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
  }
  if (dataLines.length === 0) {
    return null;
  }
  const parsed: unknown = JSON.parse(dataLines.join("\n"));
  if (!isRecord(parsed)) {
    return null;
  }
  return { type, ...parsed } as AgentStreamEvent;
}

async function streamRequest(
  path: string,
  body: Record<string, unknown>,
  onEvent: (event: AgentStreamEvent) => void
): Promise<void> {
  const token = getToken();
  const headers = new Headers();
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  if (!response.body) {
    throw new Error("浏览器不支持流式响应读取");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      const event = parseAgentSseBlock(block);
      if (event) {
        onEvent(event);
      }
    }
  }
  buffer += decoder.decode();
  const event = parseAgentSseBlock(buffer);
  if (event) {
    onEvent(event);
  }
}

export const api = {
  login: (email: string, password: string) =>
    apiRequest<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ email, password })
    }),
  register: (name: string, email: string, password: string) =>
    apiRequest<TokenResponse>("/api/v1/auth/register", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ name, email, password })
    }),
  getProfile: () => apiRequest<HealthProfile>("/api/v1/profile/me"),
  saveProfile: (payload: HealthProfile) =>
    apiRequest<HealthProfile>("/api/v1/profile/me", {
      method: "PUT",
      body: JSON.stringify(payload)
    }),
  getFitnessProfile: () => apiRequest<FitnessProfile>("/api/v1/fitness-profile/me"),
  saveFitnessProfile: (payload: FitnessProfile) =>
    apiRequest<FitnessProfile>("/api/v1/fitness-profile/me", {
      method: "PUT",
      body: JSON.stringify(payload)
    }),
  listGoals: () => apiRequest<HealthGoal[]>("/api/v1/goals"),
  createGoal: (payload: Omit<HealthGoal, "id">) =>
    apiRequest<HealthGoal>("/api/v1/goals", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  listMeals: (startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return apiRequest<Meal[]>(`/api/v1/meals${suffix}`);
  },
  createMeal: (payload: Omit<Meal, "id" | "source"> & { source?: string }) =>
    apiRequest<Meal>("/api/v1/meals", {
      method: "POST",
      body: JSON.stringify({ ...payload, source: payload.source ?? "manual" })
    }),
  generateAnalysis: (analysisDate: string) =>
    apiRequest<NutritionAnalysis>("/api/v1/analysis/daily", {
      method: "POST",
      body: JSON.stringify({ analysis_date: analysisDate })
    }),
  listAnalysis: (startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return apiRequest<NutritionAnalysis[]>(`/api/v1/analysis/daily${suffix}`);
  },
  getAnalysisSummary: (startDate: string, endDate: string) =>
    apiRequest<Record<string, unknown>>(
      `/api/v1/analysis/summary?start_date=${startDate}&end_date=${endDate}`
    ),
  listRisks: () => apiRequest<RiskAlert[]>("/api/v1/risks"),
  evaluateRisks: (analysisDate: string) =>
    apiRequest<RiskAlert[]>("/api/v1/risks/evaluate", {
      method: "POST",
      body: JSON.stringify({ analysis_date: analysisDate })
    }),
  agentChat: (message: string, analysisDate: string) =>
    apiRequest<AgentRunResult>("/api/v1/agent/chat", {
      method: "POST",
      body: JSON.stringify({ message, analysis_date: analysisDate })
    }),
  streamAgentChat: (
    message: string,
    analysisDate: string,
    onEvent: (event: AgentStreamEvent) => void
  ) => streamRequest("/api/v1/agent/chat/stream", { message, analysis_date: analysisDate }, onEvent),
  listReports: () => apiRequest<Report[]>("/api/v1/reports"),
  generateReport: (payload: {
    report_type: "weekly" | "monthly";
    period_start: string;
    period_end: string;
  }) =>
    apiRequest<{ report: Report; intervention_count: number; task_enqueued: boolean }>(
      "/api/v1/reports/generate",
      {
        method: "POST",
        body: JSON.stringify({ ...payload, run_async: false, export_format: "markdown" })
      }
    ),
  listInterventions: () => apiRequest<InterventionTask[]>("/api/v1/interventions"),
  updateIntervention: (id: string, status: "open" | "in_progress" | "completed" | "skipped") =>
    apiRequest<InterventionTask>(`/api/v1/interventions/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status })
    })
};
