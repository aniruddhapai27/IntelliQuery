export function dsKey(type) {
  return `intelliquery:datasourceId:${type}`;
}

export function saveDatasourceId(type, datasourceId) {
  if (!type || !datasourceId) return;
  localStorage.setItem(dsKey(type), String(datasourceId));
}

export function loadDatasourceId(type) {
  if (!type) return null;
  return localStorage.getItem(dsKey(type));
}
