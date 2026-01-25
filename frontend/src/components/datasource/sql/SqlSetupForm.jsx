import { useMemo, useState } from "react";
import Input from "../../Input";
import Button from "../../Button";
import { datasourceAPI, formatApiError } from "../../../utils/api";
import { saveDatasourceId } from "../common/storage";

const DEFAULTS = {
  mysql: { port: 3306 },
  psql: { port: 5432 },
};

export default function SqlSetupForm({ disabled, onConnected, onConnecting }) {
  const [formData, setFormData] = useState({
    type: "mysql",
    host: "localhost",
    port: DEFAULTS.mysql.port,
    username: "",
    password: "",
    database: "",
  });
  const [apiError, setApiError] = useState("");

  const portHint = useMemo(() => {
    const p = DEFAULTS[formData.type]?.port;
    return p ? `Default: ${p}` : "";
  }, [formData.type]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === "port" ? Number(value) : value,
    }));
  };

  const connect = async (e) => {
    e.preventDefault();
    setApiError("");
    onConnecting?.(true);

    try {
      const res = await datasourceAPI.connectSql({
        type: formData.type,
        host: formData.host,
        port: Number(formData.port),
        username: formData.username,
        password: formData.password,
        database: formData.database,
      });

      // Prefer backend-provided ID, but fall back to listing datasources.
      let datasourceId = res.data?.datasource_id;
      if (!datasourceId) {
        const list = await datasourceAPI.getAll();
        const match = (list.data ?? []).find(
          (d) =>
            (d.type === formData.type || d.type === "sql") &&
            d.details?.host === formData.host &&
            d.details?.database === formData.database,
        );
        datasourceId = match?.id;
      }

      if (!datasourceId) {
        throw new Error(
          "Connected, but could not determine datasource id. Please try again.",
        );
      }

      saveDatasourceId("sql", datasourceId);
      onConnected?.(datasourceId);
    } catch (err) {
      const msg =
        formatApiError(err.response?.data) ||
        err.message ||
        "Failed to connect to SQL database.";
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

      <div>
        <label className="block text-gray-300 font-medium mb-2">
          SQL Type <span className="text-yellow-400">*</span>
        </label>
        <select
          name="type"
          value={formData.type}
          onChange={(e) => {
            const nextType = e.target.value;
            setFormData((prev) => ({
              ...prev,
              type: nextType,
              port: DEFAULTS[nextType]?.port ?? prev.port,
            }));
          }}
          disabled={disabled}
          className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
        >
          <option value="mysql">MySQL</option>
          <option value="psql">PostgreSQL</option>
        </select>
      </div>

      <Input
        label="Host"
        name="host"
        value={formData.host}
        onChange={handleChange}
        placeholder="localhost"
        disabled={disabled}
        required
      />

      <Input
        label={`Port ${portHint ? `(${portHint})` : ""}`}
        name="port"
        type="number"
        value={formData.port}
        onChange={handleChange}
        placeholder={String(DEFAULTS[formData.type]?.port ?? 0)}
        disabled={disabled}
        required
      />

      <Input
        label="Username"
        name="username"
        value={formData.username}
        onChange={handleChange}
        placeholder="db user"
        disabled={disabled}
        required
      />

      <Input
        label="Password"
        name="password"
        type="password"
        value={formData.password}
        onChange={handleChange}
        placeholder="db password"
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
