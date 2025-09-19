'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { ReasoningStep } from '../../lib/types';
import { FileText, Clock } from 'lucide-react';

interface ExecutionLogProps {
  steps: ReasoningStep[];
}

export function ExecutionLog({ steps }: ExecutionLogProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <FileText className="h-5 w-5" />
          <span>Execution Log</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {steps.map((step, index) => (
            <div
              key={index}
              className="border-l-2 border-gray-200 pl-4 py-2 relative"
            >
              {/* Timeline dot */}
              <div className="absolute -left-2 top-3 w-3 h-3 bg-blue-500 rounded-full" />

              {/* Step content */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-sm text-gray-900">
                    {step.step_name}
                  </h4>
                  <div className="flex items-center space-x-1 text-xs text-gray-500">
                    <Clock className="h-3 w-3" />
                    <span>{step.timestamp}</span>
                  </div>
                </div>
                <p className="text-xs text-gray-600">{step.description}</p>
                {step.result && (
                  <div className="text-xs text-green-700 bg-green-50 rounded px-2 py-1">
                    Result: {step.result}
                  </div>
                )}
              </div>
            </div>
          ))}
          {steps.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              No execution steps yet
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}