'use client';

import React, { useState, useEffect } from 'react';
import { QueryInput } from '../components/research/QueryInput';
import { ResearchStrategy } from '../components/research/ResearchStrategy';
import { TaskBreakdown } from '../components/research/TaskBreakdown';
import { ProgressDisplay } from '../components/research/ProgressDisplay';
import { ExecutionLog } from '../components/research/ExecutionLog';
import { ResultsDisplay } from '../components/research/ResultsDisplay';
import { Button } from '../components/ui/Button';
import { ResearchData } from '../lib/types';
import { ResearchAPIClient } from '../lib/api';
import { WebSocketManager } from '../lib/websocket';

export default function HomePage() {
  const [isLoading, setIsLoading] = useState(false);
  const [researchData, setResearchData] = useState<ResearchData | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [wsManager, setWsManager] = useState<WebSocketManager | null>(null);

  useEffect(() => {
    return () => {
      if (wsManager) {
        wsManager.disconnect();
      }
    };
  }, [wsManager]);

  const handleSubmit = async (query: string, depth: string) => {
    setIsLoading(true);
    setResearchData(null);

    try {
      // Start research
      const response = await ResearchAPIClient.startResearch(query, depth);
      const sessionId = response.session_id;
      setCurrentSessionId(sessionId);

      // Connect to WebSocket for real-time updates
      const ws = new WebSocketManager(sessionId);
      setWsManager(ws);

      ws.onMessage = (data) => {
        // Merge new data with existing data to maintain progressive rendering
        setResearchData(prevData => ({
          intent: data.intent || prevData?.intent,
          plan: data.plan || prevData?.plan,
          progress: data.progress || prevData?.progress,
          execution_log: data.execution_log || prevData?.execution_log,
          response: data.response || prevData?.response,
          sources: data.sources || prevData?.sources
        }));
      };

      ws.onComplete = (finalData) => {
        setResearchData(finalData);
        setIsLoading(false);
      };

      ws.onError = (error) => {
        console.error('WebSocket error:', error);
        setIsLoading(false);
      };

      await ws.connect();

    } catch (error) {
      console.error('Failed to start research:', error);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="flex justify-between items-center mb-8">
            <div className="text-center flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Research Agent
              </h1>
              <p className="text-gray-600">
                AI-powered research with transparent execution
              </p>
            </div>
            <Button
              onClick={() => window.location.href = '/dashboard'}
              variant="outline"
              size="sm"
              className="ml-4"
            >
              View History
            </Button>
          </div>

          {/* Query Input */}
          <div className="mb-8">
            <QueryInput onSubmit={handleSubmit} isLoading={isLoading} />
          </div>

          {/* Research Content */}
          {(isLoading || researchData) && (
            <div className="space-y-6">
              {/* Loading State */}
              {isLoading && !researchData?.plan && (
                <div className="text-center py-12">
                  <div className="inline-flex items-center space-x-2 text-blue-600">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                    <span>Initializing research...</span>
                  </div>
                </div>
              )}

              {/* Research Strategy - Shows first */}
              {researchData?.plan && (
                <div className="animate-fadeIn">
                  <ResearchStrategy plan={researchData.plan} />
                </div>
              )}

              {/* Task Breakdown - Shows second */}
              {researchData?.plan && (
                <div className="animate-fadeIn">
                  <TaskBreakdown tasks={researchData.plan.tasks} />
                </div>
              )}

              {/* Two Column Layout for Progress and Execution - Hidden for fact queries */}
              {researchData?.intent !== 'fact' && (researchData?.progress || researchData?.execution_log) && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fadeIn">
                  {/* Left Column */}
                  <div className="space-y-6">
                    {/* Progress Display */}
                    {researchData?.progress && (
                      <ProgressDisplay progress={researchData.progress} />
                    )}
                  </div>

                  {/* Right Column */}
                  <div className="space-y-6">
                    {/* Execution Log - Updates in real-time */}
                    {researchData?.execution_log && researchData.execution_log.length > 0 && (
                      <ExecutionLog steps={researchData.execution_log} />
                    )}
                  </div>
                </div>
              )}

              {/* Results Display - Shows last when complete */}
              {researchData?.response && (
                <div className="animate-fadeIn">
                  <ResultsDisplay
                    response={researchData.response}
                    sources={researchData.sources}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}