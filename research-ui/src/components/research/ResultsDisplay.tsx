'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { FileCheck, ExternalLink } from 'lucide-react';

interface Source {
  url: string;
  title: string;
  snippet?: string;
}

interface ResultsDisplayProps {
  response: string;
  sources?: Source[];
}

export function ResultsDisplay({ response, sources = [] }: ResultsDisplayProps) {
  return (
    <Card className="bg-green-50 border-green-200">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2 text-green-900">
          <FileCheck className="h-5 w-5" />
          <span>Research Results</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Main Response - Markdown */}
          <div className="prose prose-green max-w-none">
            <ReactMarkdown
              components={{
                // Custom styling for markdown elements
                h1: ({ children }) => <h1 className="text-2xl font-bold text-green-900 mb-4">{children}</h1>,
                h2: ({ children }) => <h2 className="text-xl font-semibold text-green-900 mb-3">{children}</h2>,
                h3: ({ children }) => <h3 className="text-lg font-semibold text-green-900 mb-2">{children}</h3>,
                p: ({ children }) => <p className="text-green-800 mb-3 leading-relaxed">{children}</p>,
                ul: ({ children }) => <ul className="text-green-800 mb-3 ml-4 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="text-green-800 mb-3 ml-4 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="text-green-800">{children}</li>,
                strong: ({ children }) => <strong className="font-semibold text-green-900">{children}</strong>,
                em: ({ children }) => <em className="italic text-green-700">{children}</em>,
                code: ({ children }) => <code className="bg-green-100 text-green-900 px-1 py-0.5 rounded text-sm">{children}</code>,
                blockquote: ({ children }) => <blockquote className="border-l-4 border-green-300 pl-4 py-2 bg-green-50 text-green-800 italic">{children}</blockquote>,
              }}
            >
              {response}
            </ReactMarkdown>
          </div>

          {/* Sources */}
          {sources.length > 0 && (
            <div className="border-t border-green-200 pt-4">
              <h4 className="font-medium text-green-900 mb-3">Sources</h4>
              <div className="space-y-2">
                {sources.map((source, index) => (
                  <div
                    key={index}
                    className="bg-white border border-green-200 rounded-lg p-3"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h5 className="font-medium text-sm text-gray-900 mb-1">
                          {source.title}
                        </h5>
                        {source.snippet && (
                          <p className="text-xs text-gray-600 line-clamp-2">
                            {source.snippet}
                          </p>
                        )}
                      </div>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 text-green-600 hover:text-green-800"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </div>
                    <div className="mt-2">
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-green-600 hover:underline truncate block"
                      >
                        {source.url}
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}