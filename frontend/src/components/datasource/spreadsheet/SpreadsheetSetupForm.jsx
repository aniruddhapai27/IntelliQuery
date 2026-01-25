import { useState } from "react";
import Button from "../../Button";
import { datasourceAPI, formatApiError } from "../../../utils/api";
import { saveDatasourceId } from "../common/storage";

export default function SpreadsheetSetupForm({
  disabled,
  onConnected,
  onConnecting,
}) {
  const [file, setFile] = useState(null);
  const [apiError, setApiError] = useState("");

  const upload = async (e) => {
    e.preventDefault();
    setApiError("");

    if (!file) {
      setApiError("Please select an Excel or CSV file.");
      return;
    }

    onConnecting?.(true);
    try {
      const res = await datasourceAPI.uploadPandas(file);

      let datasourceId = res.data?.datasource_id;
      if (!datasourceId) {
        const list = await datasourceAPI.getAll();
        // pick latest pandas entry (best-effort)
        const pandas = (list.data ?? []).filter((d) => d.type === "pandas");
        datasourceId = pandas[0]?.id;
      }

      if (!datasourceId) {
        throw new Error(
          "Uploaded, but could not determine datasource id. Please try again.",
        );
      }

      saveDatasourceId("spreadsheet", datasourceId);
      onConnected?.(datasourceId);
    } catch (err) {
      const msg =
        formatApiError(err.response?.data) ||
        err.message ||
        "Failed to upload file.";
      setApiError(msg);
    } finally {
      onConnecting?.(false);
    }
  };

  return (
    <form onSubmit={upload} className="space-y-4">
      {apiError && (
        <div className="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded-lg">
          {apiError}
        </div>
      )}

      <div>
        <label className="block text-gray-300 font-medium mb-2">
          Excel / CSV File <span className="text-yellow-400">*</span>
        </label>
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          disabled={disabled}
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white file:mr-4 file:px-4 file:py-2 file:rounded-md file:border-0 file:bg-yellow-600 file:text-black"
        />
        <p className="text-gray-500 text-sm mt-2">
          Upload an Excel file (xlsx/xls) or a CSV.
        </p>
      </div>

      <Button type="submit" disabled={disabled}>
        {disabled ? "Uploading..." : "Next"}
      </Button>
    </form>
  );
}
