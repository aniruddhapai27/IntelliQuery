import QueryRunner from "../common/QueryRunner";

export default function MongoQueryPanel({ datasourceId }) {
  return (
    <QueryRunner
      datasourceId={datasourceId}
      title="MongoDB Query"
      placeholder="e.g. Find orders from last month"
    />
  );
}
