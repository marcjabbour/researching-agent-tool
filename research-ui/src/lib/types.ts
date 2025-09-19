export interface ResearchTask {
  id: string;
  description: string;
  rationale: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
}

export interface ResearchPlan {
  rationale: string;
  estimated_duration: number;
  tasks: ResearchTask[];
}

export interface ReasoningStep {
  timestamp: string;
  step_name: string;
  description: string;
  result?: string;
  task_id?: string;
}

export interface ResearchProgress {
  current_stage: string;
  current_task?: string;
  tasks_completed: number;
  total_tasks: number;
  elapsed_time: number;
}

export interface ResearchState {
  query: string;
  intent: string;
  confidence: number;
  research_plan?: ResearchPlan;
  reasoning_log: ReasoningStep[];
  research_progress?: ResearchProgress;
  final_response?: string;
  processed: boolean;
}

export interface WebSocketMessage {
  type: 'status' | 'progress' | 'error';
  research_id: string;
  status: 'started' | 'completed' | 'failed';
  data?: ResearchState;
  error?: string;
}

export interface ResearchData {
  intent?: string;
  plan?: ResearchPlan;
  progress?: ResearchProgress;
  execution_log?: ReasoningStep[];
  response?: string;
  sources?: Array<{
    url: string;
    title: string;
    snippet?: string;
  }>;
}

export interface ResearchSession {
  session_id: string;
  status: 'started' | 'completed' | 'failed';
}