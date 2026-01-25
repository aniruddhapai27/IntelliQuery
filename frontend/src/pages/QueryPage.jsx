import { useMemo } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import Card from "../components/Card";
import Button from "../components/Button";

import SqlQueryPanel from "../components/datasource/sql/SqlQueryPanel";
import MongoQueryPanel from "../components/datasource/mongo/MongoQueryPanel";
import SpreadsheetQueryPanel from "../components/datasource/spreadsheet/SpreadsheetQueryPanel";
import { loadDatasourceId } from "../components/datasource/common/storage";

const typeTitle = {
  sql: "SQL",
  mongo: "MongoDB",
  spreadsheet: "Spreadsheet",
};

export default function QueryPage() {
  const navigate = useNavigate();
  const { type } = useParams();
  const location = useLocation();

  const datasourceIdFromState = location.state?.datasourceId;
  const datasourceIdFromStorage = loadDatasourceId(type);
  const datasourceId = datasourceIdFromState ?? datasourceIdFromStorage;

  const Panel = useMemo(() => {
    if (type === "sql") return SqlQueryPanel;
    if (type === "mongo") return MongoQueryPanel;
    if (type === "spreadsheet") return SpreadsheetQueryPanel;
    return null;
  }, [type]);

  if (!Panel) {
    return (
      <div className="min-h-screen bg-black pt-24 pb-12 px-4">
        <div className="max-w-4xl mx-auto">
          <Card>
            <h1 className="text-2xl font-bold text-white mb-2">
              Unsupported datasource
            </h1>
            <Button onClick={() => navigate("/dashboard")}>Back</Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black pt-24 pb-12 px-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-20 left-20 w-96 h-96 bg-yellow-600/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-yellow-600/5 rounded-full blur-3xl"></div>
      </div>

      <div className="max-w-4xl mx-auto relative z-10">
        <div className="flex items-center justify-between gap-4 mb-6 flex-wrap">
          <div>
            <h1 className="text-3xl font-bold text-white">
              Query {typeTitle[type] ?? "Datasource"}
            </h1>
            <p className="text-gray-400">
              Ask questions in natural language. IntelliQuery generates and runs
              the query.
            </p>
          </div>
          <div className="flex gap-3">
            <Button
              variant="ghost"
              onClick={() => navigate(`/datasource/${type}/setup`)}
            >
              Change Connection
            </Button>
            <Button variant="ghost" onClick={() => navigate("/dashboard")}>
              Dashboard
            </Button>
          </div>
        </div>

        <Card>
          {!datasourceId ? (
            <div>
              <p className="text-red-400 mb-4">
                No datasource selected. Please connect first.
              </p>
              <Button onClick={() => navigate(`/datasource/${type}/setup`)}>
                Go to Setup
              </Button>
            </div>
          ) : (
            <Panel datasourceId={datasourceId} />
          )}
        </Card>
      </div>
    </div>
  );
}
