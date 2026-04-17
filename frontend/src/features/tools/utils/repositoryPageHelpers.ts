import dayjs from 'dayjs';

import type {
  CodeDirectory,
  ScriptRepository,
} from '@/features/tools/api/codeRepositoryApi';
import type { DirectoryPreset } from '@/features/tools/stores/codeDirectories';

export interface DirectoryGroup extends DirectoryPreset {
  repos: ScriptRepository[];
}

export const LANGUAGE_OPTIONS = [
  'Python',
  'Shell',
  'PowerShell',
  'Go',
  'JavaScript',
  'TypeScript',
  'Java',
  'C#',
  'C++',
  'Rust',
  'SQL',
  'XML',
  'YAML',
  'JSON',
  'Bash',
];

const UNUSED_TAGS = ['用户自定义目录'];
export const BLOCKED_DIRECTORY_TITLES = ['用户自定义目录'];

export function parseKeywords(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

export function cleanTags(tags?: string[]) {
  const normalized = (tags || [])
    .map((tag) => tag?.trim())
    .filter((tag) => tag && !UNUSED_TAGS.includes(tag));
  return Array.from(new Set(normalized));
}

export function codePlaceholder(lang?: string) {
  const key = (lang || '').toLowerCase();
  if (key === 'python') return "#!/usr/bin/env python3\nprint('Hello OneAll')";
  if (key === 'shell' || key === 'bash') return '#!/bin/bash\n# 在此编写 Shell 脚本';
  if (key === 'powershell') return '# PowerShell script';
  if (key === 'go') return 'package main\n\nfunc main() {\n    // TODO\n}';
  if (key === 'javascript' || key === 'typescript') return '// JS/TS 脚本入口';
  return '在此粘贴或编写脚本代码';
}

export function matchDirectoryKey(
  repo: ScriptRepository,
  availableDirectories: Array<CodeDirectory | DirectoryPreset>
) {
  const explicit = (repo as any).directory;
  if (explicit) return explicit as string;
  const text = [repo.name, repo.language, ...(repo.tags || [])]
    .join(' ')
    .toLowerCase();
  const preset = availableDirectories.find((item) =>
    item.keywords.some((keyword) => text.includes(keyword.toLowerCase()))
  );
  return preset?.key || availableDirectories[0]?.key || '';
}

export function formatRepositoryTime(value?: string) {
  return value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '未记录';
}
