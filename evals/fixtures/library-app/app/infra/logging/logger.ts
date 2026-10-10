type Fields = Record<string, unknown>;

function write(level: 'info' | 'error', message: string, fields: Fields): void {
  process.stdout.write(JSON.stringify({ level, message, at: new Date().toISOString(), ...fields }) + '\n');
}

export const log = {
  info: (message: string, fields: Fields = {}) => write('info', message, fields),
  error: (message: string, fields: Fields = {}) => write('error', message, fields),
};
