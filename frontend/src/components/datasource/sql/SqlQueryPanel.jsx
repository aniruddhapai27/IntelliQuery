import QueryRunner from "../common/QueryRunner";

export default function SqlQueryPanel({ datasourceId }) {
  return (
    <QueryRunner
      datasourceId={datasourceId}
      title="SQL Query"
      placeholder="e.g. Show top 10 customers by total spend"
    />
  );
}
