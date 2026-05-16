import type {
  AgentRunResult,
  FitnessProfile,
  HealthGoal,
  HealthProfile,
  InterventionTask,
  Meal,
  NutritionAnalysis,
  Report,
  RiskAlert
} from "@/lib/api";

export const today = "2026-05-16";
export const weekStart = "2026-05-10";

export const demoProfile: HealthProfile = {
  age: 25,
  gender: "female",
  height_cm: 165,
  weight_kg: 62,
  sleep_hours: 6,
  bedtime: "00:30:00",
  wake_time: "07:30:00",
  activity_level: "sedentary",
  exercise_frequency: 1,
  dietary_preferences: ["食堂", "外卖", "少辣"],
  allergies: [],
  budget_level: "student"
};

export const demoFitness: FitnessProfile = {
  exercise_level: "beginner",
  weekly_frequency: 2,
  preferred_exercise: ["快走", "自重训练"],
  available_time_minutes: 45,
  fitness_goal: "fat_loss",
  contraindications: [],
  is_sedentary: true
};

export const demoGoals: HealthGoal[] = [
  {
    id: "demo-goal-fat-loss",
    goal_type: "fat_loss",
    target_weight_kg: 58,
    target_calories: 1750,
    target_protein_g: 85,
    start_date: weekStart,
    end_date: "2026-06-16",
    status: "active"
  }
];

export const demoMeals: Meal[] = [
  {
    id: "demo-meal-1",
    meal_date: today,
    meal_time: "12:30:00",
    meal_type: "lunch",
    location: "外卖",
    source: "manual",
    note: "炸鸡汉堡套餐",
    food_items: [
      {
        name: "炸鸡汉堡",
        amount: 1,
        unit: "份",
        calories: 720,
        protein_g: 28,
        fat_g: 38,
        carbs_g: 66,
        fiber_g: 3,
        sugar_g: 8,
        sodium_mg: 1300
      }
    ]
  },
  {
    id: "demo-meal-2",
    meal_date: today,
    meal_time: "21:40:00",
    meal_type: "dinner",
    location: "便利店",
    source: "manual",
    note: "奶茶和饭团",
    food_items: [
      {
        name: "奶茶",
        amount: 1,
        unit: "杯",
        calories: 420,
        protein_g: 4,
        fat_g: 12,
        carbs_g: 72,
        fiber_g: 0,
        sugar_g: 55,
        sodium_mg: 160
      },
      {
        name: "金枪鱼饭团",
        amount: 1,
        unit: "个",
        calories: 280,
        protein_g: 9,
        fat_g: 6,
        carbs_g: 46,
        fiber_g: 2,
        sugar_g: 3,
        sodium_mg: 520
      }
    ]
  }
];

export const demoAnalysis: NutritionAnalysis = {
  id: "demo-analysis",
  analysis_date: today,
  score: 61,
  totals: {
    calories: 1420,
    protein_g: 41,
    fat_g: 56,
    carbs_g: 184,
    fiber_g: 5,
    sugar_g: 66,
    sodium_mg: 1980
  },
  macro_balance: {
    protein_pct: 12,
    carbs_pct: 54,
    fat_pct: 34
  },
  evidence: {
    target_calories: 1750,
    target_protein_g: 85,
    meal_count: 2,
    risk_count: 4
  },
  summary: "今日摄入热量尚未超标，但蛋白质和膳食纤维不足，糖摄入偏高，晚餐时间偏晚。"
};

export const demoTrend: NutritionAnalysis[] = [
  { ...demoAnalysis, id: "a1", analysis_date: "2026-05-10", score: 58, totals: { ...demoAnalysis.totals, calories: 1880, protein_g: 52 } },
  { ...demoAnalysis, id: "a2", analysis_date: "2026-05-11", score: 67, totals: { ...demoAnalysis.totals, calories: 1620, protein_g: 68 } },
  { ...demoAnalysis, id: "a3", analysis_date: "2026-05-12", score: 63, totals: { ...demoAnalysis.totals, calories: 1710, protein_g: 60 } },
  { ...demoAnalysis, id: "a4", analysis_date: "2026-05-13", score: 72, totals: { ...demoAnalysis.totals, calories: 1550, protein_g: 78 } },
  { ...demoAnalysis, id: "a5", analysis_date: "2026-05-14", score: 69, totals: { ...demoAnalysis.totals, calories: 1685, protein_g: 72 } },
  { ...demoAnalysis, id: "a6", analysis_date: "2026-05-15", score: 64, totals: { ...demoAnalysis.totals, calories: 1830, protein_g: 58 } },
  demoAnalysis
];

export const demoRisks: RiskAlert[] = [
  {
    id: "risk-sugar",
    risk_type: "sugar_high",
    severity: "medium",
    title: "糖摄入偏高",
    description: "含糖饮品推高了今日糖摄入。",
    suggestion: "饮品优先选择无糖茶、白水或无糖酸奶。",
    status: "open",
    evidence: { sugar_g: 66, target_sugar_g: 50 },
    created_at: "2026-05-16T12:00:00Z"
  },
  {
    id: "risk-protein",
    risk_type: "protein_low",
    severity: "medium",
    title: "蛋白质摄入不足",
    description: "蛋白质摄入距离目标仍有差距。",
    suggestion: "下一餐补充鸡蛋、鱼虾、豆制品或牛奶。",
    status: "open",
    evidence: { protein_g: 41, target_protein_g: 85 },
    created_at: "2026-05-16T12:00:00Z"
  },
  {
    id: "risk-late-dinner",
    risk_type: "late_dinner",
    severity: "low",
    title: "晚餐时间偏晚",
    description: "晚间进食可能影响睡眠与消化。",
    suggestion: "晚餐后安排 10-20 分钟轻松步行，避免睡前高强度运动。",
    status: "open",
    evidence: { late_after: "21:00" },
    created_at: "2026-05-16T12:00:00Z"
  }
];

export const demoAgentResult: AgentRunResult = {
  run: { id: "demo-run", status: "completed" },
  assistant_message: {
    content:
      "本次 Agent 已完成饮食分析闭环。主要问题是糖摄入偏高、蛋白质不足和晚餐偏晚。下一餐建议选择少油优质蛋白、两份蔬菜和半份主食；晚间安排 15-20 分钟轻松步行。"
  },
  state: {
    nutrition_analysis: demoAnalysis,
    risks: demoRisks,
    meal_plan: {
      today_adjustment: [
        "下一餐选择鸡胸肉、豆腐或鱼虾，搭配深色蔬菜。",
        "饮品改为无糖茶或白水，暂停奶茶和甜饮。"
      ],
      tomorrow_plan: [
        "早餐：牛奶、鸡蛋、全麦主食",
        "午餐：食堂瘦肉/鱼虾 + 两份蔬菜 + 适量米饭",
        "晚餐：少油蛋白 + 蔬菜 + 少量主食"
      ]
    },
    exercise_recommendation: {
      calorie_surplus: -330,
      recommended_plan: [
        {
          type: "恢复",
          activity: "饭后轻松步行",
          duration: "20分钟",
          intensity: "低",
          reason: "晚餐偏晚，低强度活动更适合帮助消化。"
        },
        {
          type: "力量",
          activity: "深蹲、俯卧撑、平板支撑",
          duration: "15分钟",
          intensity: "中低",
          reason: "配合减脂目标维持肌肉量。"
        }
      ]
    },
    intervention_plan: {
      next_actions: ["连续记录 3 天早餐和晚餐时间", "下周优先追踪糖摄入和蛋白质达标率"]
    },
    rag_context: [{ title: "含糖饮品干预规则", source: "local nutrition guide" }]
  }
};

export const demoReports: Report[] = [
  {
    id: "demo-report",
    report_type: "weekly",
    period_start: weekStart,
    period_end: today,
    title: "周度饮食健康报告",
    status: "completed",
    summary: "本周平均评分为 65 分，糖摄入和蛋白质不足是主要干预重点。",
    metrics: {
      average_score: 65,
      average_calories: 1710,
      average_protein_g: 61,
      open_risk_count: 3
    },
    recommendations: [
      { title: "降低含糖饮品频次", action: "未来 7 天用无糖茶或白水替代奶茶。" },
      { title: "提高蛋白质达标率", action: "每天至少两餐加入优质蛋白。" }
    ],
    export_object_key: "reports/demo/weekly.md",
    export_content: "# 周度饮食健康报告\n\n本周平均评分为 65 分。"
  }
];

export const demoInterventions: InterventionTask[] = [
  {
    id: "task-1",
    title: "降低含糖饮品频次",
    risk_type: "sugar_high",
    task_type: "diet_adjustment",
    priority: "high",
    status: "open",
    scheduled_for: today,
    due_date: "2026-05-22",
    description: "未来 7 天把奶茶、甜饮替换为无糖茶、白水或无糖酸奶。"
  },
  {
    id: "task-2",
    title: "提高蛋白质达标率",
    risk_type: "protein_low",
    task_type: "nutrition_target",
    priority: "medium",
    status: "in_progress",
    scheduled_for: today,
    due_date: "2026-05-22",
    description: "每天至少安排 2 餐包含鸡蛋、鱼虾、瘦肉、豆制品或牛奶。"
  }
];

export function sumMealCalories(meals: Meal[]): number {
  return meals.reduce(
    (sum, meal) => sum + meal.food_items.reduce((mealSum, item) => mealSum + item.calories, 0),
    0
  );
}
