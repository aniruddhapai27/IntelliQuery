import QueryRunner from "../common/QueryRunner";

export default function SpreadsheetQueryPanel({ datasourceId }) {
  return (
    <QueryRunner
      datasourceId={datasourceId}
      title="Spreadsheet Query"
      placeholder="e.g. What are the top 5 products by revenue?"
    />
  );
}
