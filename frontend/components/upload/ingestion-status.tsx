export function IngestionStatus({ file }: { file: any }) {
  return <div className="flex flex-wrap gap-2 text-xs">
    <span className="badge">parse: {file.parse_status}</span>
    <span className="badge">ingest: {file.ingest_status}</span>
    <span className="badge">vector: {file.vector_status}</span>
    <span className="badge">rows: {file.row_count}</span>
    <span className="badge">chunks: {file.chunk_count}</span>
  </div>;
}

