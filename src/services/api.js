/**
 * API Service for communicating with the Flask backend
 */

/**
 * Fetch all buildings from the backend
 * @returns {Promise<Array>} Array of building objects
 */
export const fetchBuildings = async () => {
  try {
    const response = await fetch('/api/buildings');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    if (data.error) {
      console.error('Backend error:', data.error);
      return [];
    }
    return data.data || [];
  } catch (error) {
    console.error('Failed to fetch buildings:', error);
    return [];
  }
};

/**
 * Query buildings with natural language
 * @param {string} query - Natural language query
 * @returns {Promise<Object>} Result with matching_ids and filter_parsed
 */
export const queryBuildings = async (query) => {
  try {
    const response = await fetch('/api/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    if (data.error) {
      console.error('Query error:', data.error);
      return {
        matching_ids: [],
        filter_parsed: null,
        error: data.error,
      };
    }

    return {
      matching_ids: data.matching_ids || [],
      filter_parsed: data.filter_parsed,
      error: null,
    };
  } catch (error) {
    console.error('Failed to query buildings:', error);
    return {
      matching_ids: [],
      filter_parsed: null,
      error: error.message,
    };
  }
};
