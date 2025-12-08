import React, { useState } from 'react';
import { queryBuildings } from '../services/api';
import './QueryPanel.css';

/**
 * Query panel for natural language queries
 */
const QueryPanel = ({ onQueryResult, buildings }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    const result = await queryBuildings(query);

    setLoading(false);

    if (result.error) {
      setError(result.error);
      setLastResult(null);
    } else {
      setLastResult(result);
      onQueryResult(result.matching_ids);
    }
  };

  const handleClear = () => {
    setQuery('');
    setLastResult(null);
    setError(null);
    onQueryResult([]);
  };

  return (
    <div className="query-panel">
      <div className="query-header">
        <h2>Query Buildings</h2>
        <p>Ask about buildings using natural language</p>
      </div>

      <form onSubmit={handleSubmit} className="query-form">
        <div className="query-input-group">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., 'buildings over 100 feet' or 'commercial buildings'"
            disabled={loading}
            className="query-input"
          />
          <button type="submit" disabled={loading || !query.trim()} className="query-button">
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {error && (
        <div className="query-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {lastResult && (
        <div className="query-result">
          <div className="result-summary">
            <strong>Found {lastResult.matching_ids.length} buildings</strong>
          </div>

          {lastResult.filter_parsed && (
            <div className="filter-details">
              <p>
                Filter: <code>{lastResult.filter_parsed.attribute}</code> {lastResult.filter_parsed.operator}{' '}
                <code>{lastResult.filter_parsed.value}</code>
              </p>
            </div>
          )}

          <button onClick={handleClear} className="clear-button">
            Clear Results
          </button>
        </div>
      )}

      <div className="example-queries">
        <h3>Example Queries:</h3>
        <ul>
          <li>"Buildings over 100 feet tall"</li>
          <li>"Downtown buildings"</li>
          <li>"Buildings built after 2010"</li>
          <li>"Buildings worth more than $1 million"</li>
        </ul>
      </div>
    </div>
  );
};

export default QueryPanel;
