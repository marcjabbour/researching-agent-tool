'use client';

import React, { useState } from 'react';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { Search } from 'lucide-react';

interface QueryInputProps {
  onSubmit: (query: string, depth: string) => void;
  isLoading?: boolean;
}

export function QueryInput({ onSubmit, isLoading = false }: QueryInputProps) {
  const [query, setQuery] = useState('');
  const [depth, setDepth] = useState('standard');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim(), depth);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex flex-col space-y-2">
        <label htmlFor="query" className="text-sm font-medium">
          Research Query
        </label>
        <div className="flex space-x-2">
          <Input
            id="query"
            type="text"
            placeholder="e.g., Create a memo for investing in Perplexity AI"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="px-4"
          >
            <Search className="h-4 w-4 mr-2" />
            {isLoading ? 'Researching...' : 'Research'}
          </Button>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <label className="text-sm font-medium">Depth:</label>
        <div className="flex space-x-2">
          {[
            { value: 'quick', label: 'Quick' },
            { value: 'standard', label: 'Standard' },
            { value: 'comprehensive', label: 'Comprehensive' }
          ].map((option) => (
            <label key={option.value} className="flex items-center space-x-1">
              <input
                type="radio"
                name="depth"
                value={option.value}
                checked={depth === option.value}
                onChange={(e) => setDepth(e.target.value)}
                disabled={isLoading}
                className="h-4 w-4"
              />
              <span className="text-sm">{option.label}</span>
            </label>
          ))}
        </div>
      </div>
    </form>
  );
}