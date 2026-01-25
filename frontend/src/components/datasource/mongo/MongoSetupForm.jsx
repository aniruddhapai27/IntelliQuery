import { useState } from "react";
import Input from "../../Input";
import Button from "../../Button";
import { datasourceAPI, formatApiError } from "../../../utils/api";
import { saveDatasourceId } from "../common/storage";

export default function MongoSetupForm({
  disabled,
  onConnected,
  onConnecting,
}) {
  const [formData, setFormData] = useState({
    uri: "mongodb://localhost:27017",
    database: "",
  });
  const [apiError, setApiError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const connect = async (e) => {
    e.preventDefault();
    setApiError("");
    onConnecting?.(true);

    try {
      const res = await datasourceAPI.connectMongo({
        uri: formData.uri,
        database: formData.database,
      });

      let datasourceId = res.data?.datasource_id;
      if (!datasourceId) {
        const list = await datasourceAPI.getAll();
        const match = (list.data ?? []).find(
          (d) =>
            d.type === "mongo" && d.details?.database === formData.database,
        );
        datasourceId = match?.id;
      }

      if (!datasourceId) {
        throw new Error(
          "Connected, but could not determine datasource id. Please try again.",
        );
      }

      saveDatasourceId("mongo", datasourceId);
      onConnected?.(datasourceId);
    } catch (err) {
      const msg =
        formatApiError(err.response?.data) ||
        err.message ||
        "Failed to connect to MongoDB.";
      setApiError(msg);
    } finally {
      onConnecting?.(false);
    }
  };

  return (
    <form onSubmit={connect} className="space-y-4">
      {apiError && (
        <div className="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded-lg">
          {apiError}
        </div>
      )}

      <Input
        label="MongoDB URI"
        name="uri"
        value={formData.uri}
        onChange={handleChange}
        placeholder="mongodb://user:pass@host:27017"
        disabled={disabled}
        required
      />

      <Input
        label="Database"
        name="database"
        value={formData.database}
        onChange={handleChange}
        placeholder="database name"
        disabled={disabled}
        required
      />

      <Button type="submit" disabled={disabled}>
        {disabled ? "Connecting..." : "Next"}
      </Button>
    </form>
  );
}
