export type UploadedFile = {
  id: number; file_name: string; file_type: string; file_size: number;
  detected_data_type: string; parse_status: string; ingest_status: string; vector_status: string;
  row_count: number; chunk_count: number; schema: any; preview: any[];
};
