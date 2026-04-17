let xlsxModulePromise: Promise<typeof import('xlsx')> | null = null;

const loadXlsxModule = () => {
  if (!xlsxModulePromise) {
    xlsxModulePromise = import('xlsx');
  }
  return xlsxModulePromise;
};

export function parseContactsInput(value: unknown): string[] {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value
      .map((item) => (item == null ? '' : String(item).trim()))
      .filter(Boolean);
  }
  return String(value)
    .split(/[,，\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function parseListInput(value: unknown): string[] {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value
      .map((item) => (item == null ? '' : String(item).trim()))
      .filter(Boolean);
  }
  return String(value)
    .split(/[,，\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function isExcelFile(file: File) {
  const name = file.name.toLowerCase();
  if (name.endsWith('.xlsx') || name.endsWith('.xls')) return true;
  if (file.type && file.type.includes('spreadsheet')) return true;
  return false;
}

export async function extractWorkbookRows(
  buffer: ArrayBuffer,
  headers: string[]
): Promise<Record<string, string>[]> {
  const XLSX = await loadXlsxModule();
  const workbook = XLSX.read(buffer, { type: 'array' });
  const sheetName = workbook.SheetNames[0];
  if (!sheetName) return [];
  const sheet = workbook.Sheets[sheetName];
  const json = XLSX.utils.sheet_to_json<Record<string, any>>(sheet, { defval: '' });
  void headers;
  return json.map((row) => {
    const mapped: Record<string, string> = {};
    Object.entries(row || {}).forEach(([key, value]) => {
      const normalizedKey = normalizeHeaderKey(key);
      if (!normalizedKey) return;
      mapped[normalizedKey] = value == null ? '' : String(value).trim();
    });
    return mapped;
  });
}

export function decodeTextBuffer(buffer: ArrayBuffer): string {
  const attempts: Array<{ label: string; fatal?: boolean }> = [
    { label: 'utf-8', fatal: true },
    { label: 'utf-16le', fatal: true },
    { label: 'utf-16be', fatal: true },
    { label: 'gb18030' }
  ];
  for (const attempt of attempts) {
    try {
      const decoder = new TextDecoder(attempt.label as any, { fatal: attempt.fatal ?? false });
      return decoder.decode(buffer);
    } catch (error) {
      continue;
    }
  }
  return new TextDecoder().decode(buffer);
}

export function parseCsvContent(content: string, expectedHeaders: string[]): Record<string, string>[] {
  const lines = content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (!lines.length) return [];
  void expectedHeaders;
  const delimiter = detectDelimiter(lines[0]);
  const headerCells = splitSeparatedLine(lines[0], delimiter).map((cell) => normalizeHeaderKey(cell));
  const rows: Record<string, string>[] = [];
  lines.slice(1).forEach((line) => {
    const row: Record<string, string> = {};
    const cells = splitSeparatedLine(line, delimiter);
    headerCells.forEach((header, idx) => {
      const key = header.trim();
      if (!key) return;
      row[key] = (cells[idx] ?? '').trim();
    });
    rows.push(row);
  });
  return rows;
}

export function isRowEmpty(row: Record<string, string>): boolean {
  const values = Object.values(row || {});
  if (!values.length) return true;
  return values.every((value) => !String(value ?? '').trim());
}

function detectDelimiter(line: string): string {
  const candidates = ['\t', ';', ','] as const;
  let best: string = ',';
  let bestCount = -1;
  for (const delimiter of candidates) {
    const count = countDelimiterOutsideQuotes(line, delimiter);
    if (count > bestCount) {
      bestCount = count;
      best = delimiter;
    }
  }
  return best;
}

function splitSeparatedLine(line: string, delimiter: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === delimiter && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current.trim());
  return result;
}

function countDelimiterOutsideQuotes(line: string, delimiter: string): number {
  let inQuotes = false;
  let count = 0;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        i += 1;
        continue;
      }
      inQuotes = !inQuotes;
      continue;
    }
    if (!inQuotes && char === delimiter) count += 1;
  }
  return count;
}

function normalizeHeaderKey(value: unknown): string {
  if (value == null) return '';
  return String(value)
    .replace(/^\uFEFF/, '')
    .replace(/\u3000/g, ' ')
    .trim();
}
