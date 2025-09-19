'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardContent } from '../../../../components/ui/Card';
import { Button } from '../../../../components/ui/Button';
import { ResearchStrategy } from '../../../../components/research/ResearchStrategy';
import { TaskBreakdown } from '../../../../components/research/TaskBreakdown';
import { ExecutionLog } from '../../../../components/research/ExecutionLog';
import { ResultsDisplay } from '../../../../components/research/ResultsDisplay';
import {
  ArrowLeft,
  Clock,
  Calendar,
  Activity,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';

interface SessionDetail {
  id: string;
  query: string;
  depth: string;
  intent: string;
  status: string;
  research_plan: any;
  execution_log: any[];
  final_response: string;
  sources: any[];
  created_at: string;
  completed_at?: string;
  duration_seconds?: number;
}

export default function SessionDetailPage() {
  const params = useParams();
  const sessionId = params?.id as string;
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (sessionId) {
      loadSessionDetail();
    }
  }, [sessionId]);

  const loadSessionDetail = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`http://localhost:8000/api/dashboard/session/${sessionId}`);

      if (!response.ok) {
        if (response.status === 404) {
          setError('Session not found');
        } else {
          setError('Failed to load session details');
        }
        return;
      }

      const data = await response.json();
      setSession(data);
    } catch (err) {
      console.error('Failed to load session detail:', err);
      setError('Failed to load session details');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />;
      default:
        return <Activity className="h-5 w-5 text-blue-600" />;
    }
  };

  const formatDuration = (seconds: number | undefined) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading session details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={() => window.location.href = '/dashboard'} variant="primary">
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Session not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-4 mb-4">
              <Button
                onClick={() => window.location.href = '/dashboard'}
                variant="outline"
                size="sm"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Dashboard
              </Button>
              <div className="flex items-center gap-2">
                {getStatusIcon(session.status)}
                <span className="text-sm font-medium text-gray-700 capitalize">
                  {session.status}
                </span>
              </div>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Research Session Details
            </h1>
            <p className="text-lg text-gray-600 mb-4">
              {session.query}
            </p>

            {/* Session Info */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-gray-500" />
                    <div>
                      <p className="text-xs text-gray-500">Created</p>
                      <p className="text-sm font-medium">{formatDate(session.created_at)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {session.completed_at && (
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <div>
                        <p className="text-xs text-gray-500">Completed</p>
                        <p className="text-sm font-medium">{formatDate(session.completed_at)}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-purple-500" />
                    <div>
                      <p className="text-xs text-gray-500">Duration</p>
                      <p className="text-sm font-medium">{formatDuration(session.duration_seconds)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4 text-blue-500" />
                    <div>
                      <p className="text-xs text-gray-500">Depth</p>
                      <p className="text-sm font-medium capitalize">{session.depth}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Research Content */}
          <div className="space-y-6">
            {/* Research Strategy */}
            {session.research_plan && (
              <div className="animate-fadeIn">
                <ResearchStrategy plan={session.research_plan} />
              </div>
            )}

            {/* Task Breakdown */}
            {session.research_plan && (
              <div className="animate-fadeIn">
                <TaskBreakdown tasks={session.research_plan.tasks} />
              </div>
            )}

            {/* Results Display */}
            {session.final_response && (
              <div className="animate-fadeIn">
                <ResultsDisplay
                  response={session.final_response}
                  sources={session.sources || []}
                />
              </div>
            )}

            {/* No Content Message */}
            {!session.research_plan && !session.execution_log && !session.final_response && (
              <Card>
                <CardContent className="p-12 text-center">
                  <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Research Data</h3>
                  <p className="text-gray-600">
                    This session doesn't contain detailed research data.
                    It may have failed before generating results.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}