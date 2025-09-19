'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { ResearchTask } from '../../lib/types';
import { CheckCircle, Clock, AlertCircle, Loader2 } from 'lucide-react';

interface TaskBreakdownProps {
  tasks: ResearchTask[];
}

function TaskStatus({ status }: { status: ResearchTask['status'] }) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    case 'in_progress':
      return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
    case 'failed':
      return <AlertCircle className="h-4 w-4 text-red-600" />;
    default:
      return <Clock className="h-4 w-4 text-gray-400" />;
  }
}

export function TaskBreakdown({ tasks }: TaskBreakdownProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Task Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {tasks.map((task, index) => (
            <div
              key={task.id}
              className="border-l-4 border-blue-200 pl-4 py-2"
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-sm">
                  {index + 1}. {task.description}
                </h4>
                <TaskStatus status={task.status} />
              </div>
              <p className="text-xs text-gray-600">{task.rationale}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}