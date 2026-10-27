import { mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';

export function createJsonFilePersistence(filePath) {
  return {
    load() {
      try {
        return JSON.parse(readFileSync(filePath, 'utf8'));
      } catch (error) {
        if (error.code === 'ENOENT') return undefined;
        throw error;
      }
    },
    save(state) {
      mkdirSync(dirname(filePath), { recursive: true });
      const tmpPath = `${filePath}.tmp`;
      writeFileSync(tmpPath, JSON.stringify(state, null, 2));
      renameSync(tmpPath, filePath);
    }
  };
}
