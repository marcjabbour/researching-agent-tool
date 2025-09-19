'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { ResearchProgress } from '../../lib/types';
import { Clock, TrendingUp } from 'lucide-react';

interface ProgressDisplayProps {
  progress: ResearchProgress;
}

export function ProgressDisplay({ progress }: ProgressDisplayProps) {
  const completedTasks = progress.tasks_completed;
  const totalTasks = progress.total_tasks;
  const progressPercentage = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <TrendingUp className="h-5 w-5" />
          <span>Research Progress</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>

          {/* Progress Stats */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Tasks Completed:</span>
              <div className="font-semibold">{completedTasks} / {totalTasks}</div>
            </div>
            <div className="flex items-center space-x-1">
              <Clock className="h-4 w-4 text-gray-500" />
              <span className="text-gray-600">Elapsed:</span>
              <div className="font-semibold">{progress.elapsed_time}s</div>
            </div>
          </div>

          {/* Current Status */}
          {progress.current_task && (
            <div className="border-t pt-3">
              <span className="text-sm text-gray-600">Currently working on:</span>
              <div className="font-medium text-blue-700">{progress.current_task}</div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}