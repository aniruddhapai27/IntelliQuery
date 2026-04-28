import { useState, useEffect, useCallback, useMemo } from "react";
import { aiAPI } from "../../../utils/api";

// Chart type icons mapping
const chartIcons = {
  line: "📈",
  bar: "📊",
  horizontal_bar: "📊",
  pie: "🥧",
  scatter: "⚬",
  histogram: "📊",
  box: "📦",
  area: "📉",
  stacked_bar: "📊",
  grouped_bar: "📊",
  heatmap: "🗺️",
  funnel: "🔻",
  waterfall: "💧",
};

// Chart type display names
const chartNames = {
  line: "Line Chart",
  bar: "Bar Chart",
  horizontal_bar: "Horizontal Bar",
  pie: "Pie Chart",
  scatter: "Scatter Plot",
  histogram: "Histogram",
  box: "Box Plot",
  area: "Area Chart",
  stacked_bar: "Stacked Bar",
  grouped_bar: "Grouped Bar",
  heatmap: "Heatmap",
  funnel: "Funnel Chart",
  waterfall: "Waterfall",
};

// Lazy load Plotly for performance
let Plot = null;
const loadPlotly = async () => {
  if (!Plot) {
    const module = await import("react-plotly.js");
    Plot = module.default;
  }
  return Plot;
};

export default function VisualizationPanel({ results, queryContext, onChartDataChange }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [suggestions, setSuggestions] = useState(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [selectedChart, setSelectedChart] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loadingChart, setLoadingChart] = useState(false);
  const [error, setError] = useState(null);
  const [PlotComponent, setPlotComponent] = useState(null);
  const [customization, setCustomization] = useState({
    theme: "plotly_dark",
    height: 400,
    width: null, // Auto
  });

  // Don't render if no results or results is empty
  const hasData = useMemo(() => {
    return results && Array.isArray(results) && results.length > 0;
  }, [results]);

  // Load Plotly when expanded
  useEffect(() => {
    if (isExpanded && !PlotComponent) {
      loadPlotly().then((P) => setPlotComponent(() => P));
    }
  }, [isExpanded, PlotComponent]);

  // Fetch suggestions when panel is expanded (only once)
  useEffect(() => {
    if (!isExpanded || !hasData || suggestions || loadingSuggestions) return;

    const fetchSuggestions = async () => {
      setLoadingSuggestions(true);
      setError(null);

      try {
        const res = await aiAPI.suggestVisualizations({
          results: results.slice(0, 100), // Limit for API
          query_context: queryContext || "",
        });

        if (res.data.success) {
          setSuggestions(res.data);
          // Auto-select the first recommendation
          if (res.data.recommendations?.length > 0) {
            setSelectedChart(res.data.recommendations[0]);
          }
        } else {
          setError(res.data.error || "Failed to get suggestions");
        }
      } catch (err) {
        console.error("Visualization suggestion error:", err);
        setError("Failed to analyze data for visualization");
      } finally {
        setLoadingSuggestions(false);
      }
    };

    fetchSuggestions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isExpanded]);

  // Generate chart when selection changes (only once per selection)
  useEffect(() => {
    if (!selectedChart || !isExpanded || !PlotComponent || loadingChart) return;

    // Check if we already have this chart data to avoid re-generating
    if (chartData && chartData.chart_type === selectedChart.type) return;

    const generateChart = async () => {
      setLoadingChart(true);
      setError(null);

      try {
        const res = await aiAPI.generateVisualization({
          results: results.slice(0, 500), // More data for actual chart
          chart_type: selectedChart.type,
          x_axis: selectedChart.x_axis || null,
          y_axis: selectedChart.y_axis || null,
          group_by: selectedChart.group_by || null,
          customization: customization,
        });

        if (res.data.success) {
          setChartData(res.data);
          onChartDataChange?.(res.data.chart_data || null);
        } else {
          setError(res.data.error || "Failed to generate chart");
        }
      } catch (err) {
        console.error("Chart generation error:", err);
        setError("Failed to generate visualization");
      } finally {
        setLoadingChart(false);
      }
    };

    generateChart();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedChart?.type, PlotComponent, isExpanded]);

  // Handle chart type selection
  const handleChartSelect = (recommendation) => {
    setSelectedChart(recommendation);
    setChartData(null); // Clear previous chart
  };

  // Toggle expansion
  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  if (!hasData) return null;

  return (
    <div className="mt-4 border border-gray-700 rounded-lg overflow-hidden">
      {/* Header - Always visible */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-800/50 hover:bg-gray-800 transition-colors duration-200"
      >
        <div className="flex items-center space-x-2">
          <span className="text-lg">📊</span>
          <span className="text-sm font-medium text-gray-200">
            Visualize Data
          </span>
          {suggestions?.data_summary && (
            <span className="text-xs text-gray-500">
              ({suggestions.data_summary.rows} rows,{" "}
              {suggestions.data_summary.columns} columns)
            </span>
          )}
        </div>
        <svg
          className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${
            isExpanded ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-4 bg-gray-900/50 space-y-4">
          {/* Loading Suggestions */}
          {loadingSuggestions && (
            <div className="flex items-center justify-center py-8">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-yellow-600 border-t-transparent"></div>
                <span className="text-sm text-gray-400">
                  Analyzing data for best visualizations...
                </span>
              </div>
            </div>
          )}

          {/* Error - No Graph Available */}
          {error && !loadingSuggestions && !loadingChart && (
            <div className="flex flex-col items-center justify-center py-12 bg-gray-800/30 rounded-lg border border-gray-700">
              <div className="text-6xl mb-4 opacity-50">📊</div>
              <p className="text-lg font-medium text-gray-400 mb-2">
                No Graph Available
              </p>
              <p className="text-sm text-gray-500 text-center max-w-md">
                {error}
              </p>
            </div>
          )}

          {/* Data Insights */}
          {suggestions?.data_insights && (
            <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700">
              <p className="text-xs text-gray-400 mb-1">Data Insights</p>
              <p className="text-sm text-gray-300">
                {suggestions.data_insights}
              </p>
            </div>
          )}

          {/* No recommendations available */}
          {!error &&
            suggestions &&
            suggestions.recommendations?.length === 0 &&
            !loadingSuggestions && (
              <div className="flex flex-col items-center justify-center py-12 bg-gray-800/30 rounded-lg border border-gray-700">
                <div className="text-6xl mb-4 opacity-50">📊</div>
                <p className="text-lg font-medium text-gray-400 mb-2">
                  No Graph Available
                </p>
                <p className="text-sm text-gray-500 text-center max-w-md">
                  Unable to generate visualizations for this data.
                </p>
              </div>
            )}

          {/* Chart Type Selection */}
          {!error && suggestions?.recommendations?.length > 0 && (
            <div>
              <p className="text-xs text-gray-400 mb-2">
                Recommended Visualizations
              </p>
              <div className="flex flex-wrap gap-2">
                {suggestions.recommendations.map((rec, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleChartSelect(rec)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg border text-sm transition-all duration-200 ${
                      selectedChart?.type === rec.type
                        ? "bg-yellow-600/20 border-yellow-600 text-yellow-500"
                        : "bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600"
                    }`}
                    title={rec.reason}
                  >
                    <span>{chartIcons[rec.type] || "📊"}</span>
                    <span>{chartNames[rec.type] || rec.type}</span>
                    {rec.priority === 1 && (
                      <span className="text-xs bg-yellow-600/30 text-yellow-500 px-1.5 py-0.5 rounded">
                        Best
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Selected Chart Info */}
          {!error && selectedChart && (
            <div className="text-xs text-gray-500 flex flex-wrap gap-x-4 gap-y-1">
              {selectedChart.x_axis && (
                <span>
                  X-Axis:{" "}
                  <span className="text-gray-400">{selectedChart.x_axis}</span>
                </span>
              )}
              {selectedChart.y_axis && (
                <span>
                  Y-Axis:{" "}
                  <span className="text-gray-400">{selectedChart.y_axis}</span>
                </span>
              )}
              {selectedChart.group_by && (
                <span>
                  Group By:{" "}
                  <span className="text-gray-400">
                    {selectedChart.group_by}
                  </span>
                </span>
              )}
              {selectedChart.reason && (
                <span className="italic text-gray-500">
                  — {selectedChart.reason}
                </span>
              )}
            </div>
          )}

          {/* Chart Display */}
          {!error && loadingChart && (
            <div className="flex items-center justify-center py-12 bg-gray-800/30 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-6 w-6 border-2 border-yellow-600 border-t-transparent"></div>
                <span className="text-sm text-gray-400">
                  Generating visualization...
                </span>
              </div>
            </div>
          )}

          {!error &&
            chartData?.chart_data &&
            PlotComponent &&
            !loadingChart && (
              <div className="bg-gray-900 rounded-lg overflow-hidden border border-gray-700">
                <PlotComponent
                  data={chartData.chart_data.data}
                  layout={{
                    ...chartData.chart_data.layout,
                    paper_bgcolor: "rgba(0,0,0,0)",
                    plot_bgcolor: "rgba(17,24,39,1)",
                    font: { color: "#9CA3AF" },
                    autosize: true,
                    margin: { l: 50, r: 30, t: 50, b: 50 },
                  }}
                  config={{
                    ...chartData.config,
                    displayModeBar: true,
                    displaylogo: false,
                    responsive: true,
                    modeBarButtonsToRemove: ["lasso2d", "select2d"],
                  }}
                  style={{ width: "100%", height: "400px" }}
                  useResizeHandler={true}
                />
              </div>
            )}

          {/* Customization Options (collapsible) */}
          {!error && chartData && (
            <details className="text-sm">
              <summary className="cursor-pointer text-gray-400 hover:text-gray-300">
                Chart Options
              </summary>
              <div className="mt-2 flex flex-wrap gap-4 p-3 bg-gray-800/30 rounded-lg">
                <label className="flex items-center space-x-2 text-gray-400">
                  <span className="text-xs">Theme:</span>
                  <select
                    value={customization.theme}
                    onChange={(e) =>
                      setCustomization((prev) => ({
                        ...prev,
                        theme: e.target.value,
                      }))
                    }
                    className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-300"
                  >
                    <option value="plotly_dark">Dark</option>
                    <option value="plotly_white">Light</option>
                    <option value="seaborn">Seaborn</option>
                    <option value="ggplot2">ggplot2</option>
                  </select>
                </label>
                <label className="flex items-center space-x-2 text-gray-400">
                  <span className="text-xs">Height:</span>
                  <select
                    value={customization.height}
                    onChange={(e) =>
                      setCustomization((prev) => ({
                        ...prev,
                        height: parseInt(e.target.value),
                      }))
                    }
                    className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-300"
                  >
                    <option value={300}>Small (300px)</option>
                    <option value={400}>Medium (400px)</option>
                    <option value={500}>Large (500px)</option>
                    <option value={600}>Extra Large (600px)</option>
                  </select>
                </label>
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
