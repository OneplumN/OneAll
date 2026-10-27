export type CompileIpRegexResult = {
  regex: string;
  matchedCount: number;
  duplicateCount: number;
  invalidIps: string[];
  normalizedIps: string[];
};

export type ExpandIpRegexResult = {
  ips: string[];
  count: number;
  limit: number;
  truncated: boolean;
};

const ipv4Pattern = /^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$/;

export function isValidIpv4(value: string) {
  return ipv4Pattern.test(value.trim());
}

export function parseIpLines(input: string) {
  return input
    .split(/[\s,;，；]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function combinePatternList(patterns: string[]) {
  if (!patterns.length) throw new Error('模式列表不能为空');
  return patterns.length === 1 ? patterns[0] : `(${patterns.join('|')})`;
}

function shouldUsePipeNotation(startNum: number, endNum: number) {
  if (String(startNum).length !== String(endNum).length) return true;
  if (Math.floor(startNum / 10) !== Math.floor(endNum / 10)) return true;
  return endNum - startNum > 10;
}

function createRangePattern(startNum: number, endNum: number) {
  if (shouldUsePipeNotation(startNum, endNum)) {
    return `(${Array.from({ length: endNum - startNum + 1 }, (_, index) => String(startNum + index)).join('|')})`;
  }
  return `[${startNum}-${endNum}]`;
}

function findRanges(digits: number[]) {
  const ranges: number[][] = [];
  let current: number[] = [];
  for (const digit of digits) {
    if (!current.length || digit === current[current.length - 1] + 1) {
      current.push(digit);
    } else {
      ranges.push(current);
      current = [digit];
    }
  }
  if (current.length) ranges.push(current);
  return ranges;
}

function buildRangeParts(ranges: number[][]) {
  const parts: string[] = [];
  for (const range of ranges) {
    if (range.length >= 2) {
      const pattern = createRangePattern(range[0], range[range.length - 1]);
      parts.push(pattern.startsWith('[') && pattern.endsWith(']') ? pattern.slice(1, -1) : pattern);
    } else {
      parts.push(String(range[0]));
    }
  }
  return parts;
}

function formatPrefixRange(prefix: number, rangeParts: string[]) {
  const prefixText = String(prefix);
  if (rangeParts.length === 1) {
    const part = rangeParts[0];
    if (part.startsWith('(') && part.endsWith(')')) return `${prefixText}${part}`;
    if (part.includes('-')) return `${prefixText}[${part}]`;
    return `${prefixText}${part}`;
  }
  return `${prefixText}[${rangeParts.join('|')}]`;
}

function processLastOctets(lastOctets: string[]) {
  const numbers = [...new Set(lastOctets.map((item) => Number(item)))].sort((a, b) => a - b);
  const patterns: string[] = [];

  if (numbers.length === 2 && numbers[1] === numbers[0] + 1) {
    const [first, second] = numbers;
    if (first >= 100) {
      if (Math.floor(first / 10) === Math.floor(second / 10)) {
        patterns.push(`${Math.floor(first / 10)}[${first % 10}-${second % 10}]`);
        return patterns;
      }
      patterns.push(`(${first}|${second})`);
      return patterns;
    }
    if (first >= 10) {
      if (Math.floor(first / 10) === Math.floor(second / 10)) {
        patterns.push(`${Math.floor(first / 10)}[${first % 10}-${second % 10}]`);
        return patterns;
      }
      patterns.push(`(${first}|${second})`);
      return patterns;
    }
    patterns.push(createRangePattern(first, second));
    return patterns;
  }

  if (numbers.length > 1) {
    const byHundreds = new Map<number, number[]>();
    const byTens = new Map<number, number[]>();
    const units: number[] = [];

    for (const number of numbers) {
      if (number >= 100) {
        const prefix = Math.floor(number / 10);
        byHundreds.set(prefix, [...(byHundreds.get(prefix) ?? []), number % 10]);
      } else if (number >= 10) {
        const tens = Math.floor(number / 10);
        byTens.set(tens, [...(byTens.get(tens) ?? []), number % 10]);
      } else {
        units.push(number);
      }
    }

    for (const [prefix, digits] of byHundreds) {
      digits.sort((a, b) => a - b);
      patterns.push(formatPrefixRange(prefix, buildRangeParts(findRanges(digits))));
    }
    for (const [tens, digits] of byTens) {
      digits.sort((a, b) => a - b);
      patterns.push(formatPrefixRange(tens, buildRangeParts(findRanges(digits))));
    }
    if (units.length) {
      for (const range of findRanges(units.sort((a, b) => a - b))) {
        if (range.length >= 2) patterns.push(createRangePattern(range[0], range[range.length - 1]));
        else patterns.push(String(range[0]));
      }
    }
  } else if (numbers.length === 1) {
    patterns.push(String(numbers[0]));
  }

  return patterns;
}

export function compileIpRegexFromText(input: string): CompileIpRegexResult {
  const seen = new Set<string>();
  const invalidIps: string[] = [];
  const normalizedIps: string[] = [];
  let duplicateCount = 0;

  for (const item of parseIpLines(input)) {
    if (!isValidIpv4(item)) {
      invalidIps.push(item);
      continue;
    }
    if (!seen.has(item)) {
      seen.add(item);
      normalizedIps.push(item);
    } else {
      duplicateCount += 1;
    }
  }

  const aGroups = new Map<string, Map<string, Map<string, Set<string>>>>();
  for (const ip of normalizedIps) {
    const [a, b, c, d] = ip.split('.');
    if (!aGroups.has(a)) aGroups.set(a, new Map());
    const bGroups = aGroups.get(a)!;
    if (!bGroups.has(b)) bGroups.set(b, new Map());
    const cGroups = bGroups.get(b)!;
    if (!cGroups.has(c)) cGroups.set(c, new Set());
    cGroups.get(c)!.add(d);
  }

  const mainPatterns: string[] = [];
  for (const [aOctet, bGroups] of aGroups) {
    const structureGroups = new Map<string, { expression: string; bValues: Set<string> }>();

    for (const [bOctet, cGroups] of bGroups) {
      const cPatterns: string[] = [];
      const cSignature: Array<[string, string[]]> = [];
      const sortedCGroups = [...cGroups.entries()].sort(([left], [right]) => Number(left) - Number(right));

      for (const [cOctet, dOctets] of sortedCGroups) {
        const dPatterns = processLastOctets([...dOctets]);
        const dExpression = combinePatternList(dPatterns);
        cPatterns.push(`${cOctet}\\.${dExpression}`);
        cSignature.push([cOctet, dPatterns]);
      }

      const cdExpression = combinePatternList(cPatterns);
      const key = JSON.stringify(cSignature);
      const group = structureGroups.get(key) ?? { expression: cdExpression, bValues: new Set<string>() };
      group.bValues.add(bOctet);
      structureGroups.set(key, group);
    }

    const aPatterns = [...structureGroups.values()]
      .sort((left, right) => Math.min(...[...left.bValues].map(Number)) - Math.min(...[...right.bValues].map(Number)))
      .map((group) => `${combinePatternList(processLastOctets([...group.bValues]))}\\.${group.expression}`);

    mainPatterns.push(`(${aOctet}\\.${combinePatternList(aPatterns)})`);
  }

  return {
    regex: mainPatterns.join('|'),
    matchedCount: normalizedIps.length,
    duplicateCount,
    invalidIps,
    normalizedIps
  };
}

function combineSegments(prefixes: string[], suffixes: string[], limit: number) {
  const combined: string[] = [];
  const seen = new Set<string>();
  for (const prefix of prefixes) {
    for (const suffix of suffixes) {
      const value = `${prefix}${suffix}`;
      if (!seen.has(value)) {
        if (combined.length >= limit) throw new Error(`反推结果数量超过限制 ${limit}`);
        combined.push(value);
        seen.add(value);
      }
    }
  }
  return combined;
}

function splitTopLevelBranches(source: string) {
  const branches: string[] = [];
  let depth = 0;
  let inClass = false;
  let escaped = false;
  let start = 0;

  for (let index = 0; index < source.length; index += 1) {
    const char = source[index];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === '\\') {
      escaped = true;
      continue;
    }
    if (char === '[' && !inClass) {
      inClass = true;
      continue;
    }
    if (char === ']' && inClass) {
      inClass = false;
      continue;
    }
    if (inClass) continue;
    if (char === '(') depth += 1;
    if (char === ')') depth -= 1;
    if (char === '|' && depth === 0) {
      branches.push(source.slice(start, index));
      start = index + 1;
    }
  }

  branches.push(source.slice(start));
  return branches;
}

function findClosing(source: string, startIndex: number, open: string, close: string) {
  let depth = 0;
  let escaped = false;
  for (let index = startIndex; index < source.length; index += 1) {
    const char = source[index];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === '\\') {
      escaped = true;
      continue;
    }
    if (char === open) depth += 1;
    if (char === close) {
      depth -= 1;
      if (depth === 0) return index;
    }
  }
  return -1;
}

function expandCharacterClass(body: string) {
  const values: string[] = [];
  for (let index = 0; index < body.length; index += 1) {
    const current = body[index];
    if (current === '|') continue;
    if (index + 2 < body.length && body[index + 1] === '-') {
      const start = body.charCodeAt(index);
      const end = body.charCodeAt(index + 2);
      if (start > end) throw new Error('字符范围格式不合法');
      for (let code = start; code <= end; code += 1) values.push(String.fromCharCode(code));
      index += 2;
    } else {
      values.push(current);
    }
  }
  return [...new Set(values)];
}

function expandRegexExpression(source: string, limit: number): string[] {
  const branches = splitTopLevelBranches(source);
  if (branches.length > 1) {
    const merged: string[] = [];
    const seen = new Set<string>();
    for (const branch of branches) {
      for (const value of expandRegexExpression(branch, limit)) {
        if (!seen.has(value)) {
          if (merged.length >= limit) throw new Error(`反推结果数量超过限制 ${limit}`);
          merged.push(value);
          seen.add(value);
        }
      }
    }
    return merged;
  }

  let results = [''];
  for (let index = 0; index < source.length; index += 1) {
    const char = source[index];
    if (['*', '+', '?', '{', '}'].includes(char)) {
      throw new Error('当前工具不支持包含重复量词的正则表达式');
    }
    if (char === '\\') {
      if (index + 1 >= source.length) throw new Error('正则表达式转义不完整');
      results = combineSegments(results, [source[index + 1]], limit);
      index += 1;
      continue;
    }
    if (char === '(') {
      const end = findClosing(source, index, '(', ')');
      if (end < 0) throw new Error('正则表达式括号不闭合');
      const options = expandRegexExpression(source.slice(index + 1, end), limit);
      results = combineSegments(results, options, limit);
      index = end;
      continue;
    }
    if (char === '[') {
      const end = source.indexOf(']', index + 1);
      if (end < 0) throw new Error('正则表达式字符集不闭合');
      results = combineSegments(results, expandCharacterClass(source.slice(index + 1, end)), limit);
      index = end;
      continue;
    }
    if (char === '^' || char === '$') continue;
    results = combineSegments(results, [char], limit);
  }
  return results;
}

export function expandIpRegex(pattern: string, limit = 500): ExpandIpRegexResult {
  const safeLimit = Math.max(1, Math.min(Math.floor(limit), 2000));
  const source = pattern.trim();
  if (!source) return { ips: [], count: 0, limit: safeLimit, truncated: false };

  const expanded = expandRegexExpression(source.replace(/^\^/, '').replace(/\$$/, ''), safeLimit + 1);
  const ips = [...new Set(expanded.filter((item) => isValidIpv4(item)))].sort((left, right) => {
    const leftParts = left.split('.').map(Number);
    const rightParts = right.split('.').map(Number);
    for (let index = 0; index < 4; index += 1) {
      if (leftParts[index] !== rightParts[index]) return leftParts[index] - rightParts[index];
    }
    return 0;
  });

  return {
    ips: ips.slice(0, safeLimit),
    count: ips.length,
    limit: safeLimit,
    truncated: ips.length > safeLimit
  };
}

export function testIpAgainstRegex(ip: string, pattern: string) {
  const target = ip.trim();
  const source = pattern.trim();

  if (!isValidIpv4(target)) {
    return { matched: false, validIp: false, error: '请输入合法 IPv4 地址' };
  }

  if (!source) {
    return { matched: false, validIp: true, error: '请先输入或生成正则表达式' };
  }

  try {
    return { matched: new RegExp(source).test(target), validIp: true, error: '' };
  } catch {
    return { matched: false, validIp: true, error: '正则表达式格式不合法' };
  }
}
