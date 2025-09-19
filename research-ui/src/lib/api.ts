import { ResearchSession } from './types';

const API_BASE_URL = 'http://localhost:8001';

export interface StartResearchRequest {
  query: string;
  depth?: string;
}

export class ResearchAPIClient {
  static async startResearch(query: string, depth: string = 'standard'): Promise<ResearchSession> {
    const response = await fetch(`${API_BASE_URL}/api/research`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, depth }),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    const data = await response.json();
    // Backend returns research_id, frontend expects session_id
    return {
      session_id: data.research_id,
      status: data.status
    };
  }

  static async getResearchStatus(sessionId: string) {
    const response = await fetch(`${API_BASE_URL}/api/research/${sessionId}`);

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }
}