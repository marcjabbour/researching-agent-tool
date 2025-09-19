import { WebSocketMessage, ResearchData } from './types';

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(private sessionId: string) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`ws://localhost:8001/ws/research/${this.sessionId}`);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
            console.error('Raw message data:', event.data);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          this.handleReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(message: WebSocketMessage) {
    console.log('WebSocket message received:', message);

    try {
      // Handle fact queries that complete immediately
      if (message.type === 'status' && message.status === 'completed') {
        this.onComplete?.(this.transformData(message.data));
        return;
      }

      // Handle messages with data
      if (message.data) {
        const researchData = this.transformData(message.data);

        switch (message.type) {
          case 'status':
            this.onMessage?.(researchData);
            if (message.status === 'completed') {
              this.onComplete?.(researchData);
            }
            break;
          case 'progress':
            this.onMessage?.(researchData);
            break;
          case 'error':
            this.onError?.(message.error || 'Unknown error');
            break;
        }
      } else {
        // Handle messages without data (like simple status updates)
        if (message.type === 'error') {
          this.onError?.(message.error || 'Unknown error');
        }
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
      console.error('Message:', message);
    }
  }

  private transformData(data: any): ResearchData {
    if (!data) {
      return {
        intent: undefined,
        plan: undefined,
        progress: undefined,
        execution_log: undefined,
        response: undefined,
        sources: []
      };
    }

    return {
      intent: data.intent || undefined,
      plan: data.research_plan || undefined,
      progress: data.research_progress ? {
        current_stage: data.research_progress.current_stage || '',
        current_task: data.research_progress.current_reasoning || '',
        tasks_completed: data.research_progress.tasks_completed || 0,
        total_tasks: data.research_progress.total_tasks || 0,
        elapsed_time: 0 // TODO: Calculate elapsed time
      } : undefined,
      execution_log: data.reasoning_log?.map((step: any) => ({
        timestamp: step.timestamp || new Date().toISOString(),
        step_name: step.stage || 'Unknown',
        description: step.reasoning || '',
        result: undefined,
        task_id: step.task_id
      })) || undefined,
      response: data.final_response || undefined,
      sources: [] // Add sources if available in the backend
    };
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      setTimeout(() => this.connect(), 1000 * this.reconnectAttempts);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // Event handlers - to be set by the consumer
  onMessage?: (data: ResearchData) => void;
  onComplete?: (data: ResearchData) => void;
  onError?: (error: string) => void;
}