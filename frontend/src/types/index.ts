// 与 backend/app/models 对齐的前端类型定义

export interface QuestionGrade {
  question_no: string
  question_type?: string
  student_answer?: string
  correct_answer?: string
  is_correct: boolean
  score: number
  max_score: number
  knowledge_point?: string
  feedback?: string
}

export interface GradingResult {
  subject: string
  student_name?: string
  total_score: number
  earned_score: number
  questions: QuestionGrade[]
  overall_comment: string
}

export interface ErrorItem {
  question_no: string
  knowledge_point?: string
  error_type: string
  cause?: string
  suggestion?: string
}

export interface ErrorAnalysis {
  errors: ErrorItem[]
  summary: string
}

export interface ErrorRecord {
  id: number
  student_id: string
  subject: string
  question_no: string
  knowledge_point: string
  error_type: string
  student_answer: string
  correct_answer: string
  cause: string
  suggestion: string
  review_count: number
  last_review_at: string
  next_review_at: string
  created_at: string
}

export interface KnowledgeMastery {
  knowledge_point: string
  attempts: number
  wrong: number
  mastery_rate: number
}

export interface LearningReport {
  scope: string
  total_gradings: number
  total_errors: number
  avg_score_rate: number
  knowledge_mastery: KnowledgeMastery[]
  error_type_dist: Record<string, number>
  weak_points: string[]
  narrative: string
}

export interface TutorReply {
  reply: string
  grounded_points: string[]
}

export interface PracticeItem {
  knowledge_point: string
  stem: string
  answer: string
  difficulty: string
  hint: string
  why: string
}

export interface PracticePlan {
  student_id: string
  items: PracticeItem[]
  plan_summary: string
}

export interface ReviewItem {
  error_id: number
  knowledge_point: string
  question_no: string
  error_type: string
  student_answer: string
  correct_answer: string
  cause: string
  suggestion: string
  review_count: number
  last_review_at: string
  next_review_at: string
  overdue_days: number
}

// 统一响应体（AgentResponse）
export interface AgentResponse {
  task: string
  student_id: string
  grading?: GradingResult | null
  error_analysis?: ErrorAnalysis | null
  saved_errors: number
  report?: LearningReport | null
  tutor_reply?: TutorReply | null
  practice_plan?: PracticePlan | null
  review_queue: ReviewItem[]
  reviewed: number
  steps: string[]
  error: string
}

export interface Health {
  status: string
  app: string
  llm_enabled: boolean
  vlm_model: string
  llm_model: string
}
