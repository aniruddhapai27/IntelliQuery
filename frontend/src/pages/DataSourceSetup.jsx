import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Card from "../components/Card";
import Button from "../components/Button";

import SqlSetupForm from "../components/datasource/sql/SqlSetupForm";
import MongoSetupForm from "../components/datasource/mongo/MongoSetupForm";
import SpreadsheetSetupForm from "../components/datasource/spreadsheet/SpreadsheetSetupForm";

const typeMeta = {
  sql: { title: "SQL", subtitle: "Connect MySQL or PostgreSQL" },
  mongo: { title: "MongoDB", subtitle: "Connect using MongoDB URI" },
  spreadsheet: {
    title: "Spreadsheet",
    subtitle: "Upload CSV/Excel for analysis",
  },
};

export default function DataSourceSetup() {
  const navigate = useNavigate();
  const { type } = useParams();
  const [connecting, setConnecting] = useState(false);

  const meta = typeMeta[type] ?? { title: "Datasource", subtitle: "" };

  const SetupForm = useMemo(() => {
    if (type === "sql") return SqlSetupForm;
    if (type === "mongo") return MongoSetupForm;
    if (type === "spreadsheet") return SpreadsheetSetupForm;
    return null;
  }, [type]);

  if (!SetupForm) {
    return (
      <div className="min-h-screen bg-black pt-24 pb-12 px-4">
        <div className="max-w-3xl mx-auto">
          <Card>
            <h1 className="text-2xl font-bold text-white mb-2">
              Unsupported datasource
            </h1>
            <p className="text-gray-400 mb-6">
              Please go back to dashboard and pick SQL, Mongo, or Spreadsheet.
            </p>
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

      <div className="max-w-3xl mx-auto relative z-10">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white">
            Connect {meta.title}
          </h1>
          <p className="text-gray-400">{meta.subtitle}</p>
        </div>

        <Card>
          <SetupForm
            disabled={connecting}
            onConnecting={(v) => setConnecting(v)}
            onConnected={(datasourceId) => {
              // Navigate to common query page with datasourceId
              navigate(`/datasource/${type}/query`, {
                state: { datasourceId },
              });
            }}
          />
        </Card>

        <div className="mt-6">
          <Button variant="ghost" onClick={() => navigate("/dashboard")}>
            Back to Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
}
