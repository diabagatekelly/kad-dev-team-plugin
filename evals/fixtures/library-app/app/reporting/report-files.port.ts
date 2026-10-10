export interface ReportFiles {
  write(path: string, contents: string): Promise<void>;
}
