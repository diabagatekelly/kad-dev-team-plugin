import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import type { ReportFiles } from '../../reporting/report-files.port';

export class LocalReportFiles implements ReportFiles {
  constructor(private readonly root: string) {}

  async write(path: string, contents: string): Promise<void> {
    const target = join(this.root, path);
    await mkdir(dirname(target), { recursive: true });
    await writeFile(target, contents, 'utf8');
  }
}
