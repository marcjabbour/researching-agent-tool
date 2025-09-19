'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { ResearchPlan } from '../../lib/types';
import { Clock, Target } from 'lucide-react';

interface ResearchStrategyProps {
  plan: ResearchPlan;
}

export function ResearchStrategy({ plan }: ResearchStrategyProps) {
  return (
    <Card className="bg-blue-50 border-blue-200">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2 text-blue-900">
          <Target className="h-5 w-5" />
          <span>Research Strategy</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-blue-800 mb-4">{plan.rationale}</p>
        <div className="flex items-center space-x-4 text-sm text-blue-700">
          <div className="flex items-center space-x-1">
            <Clock className="h-4 w-4" />
            <span>Est. {plan.estimated_duration}s</span>
          </div>
          <div>
            {plan.tasks.length} parallel tasks
          </div>
        </div>
      </CardContent>
    </Card>
  );
}