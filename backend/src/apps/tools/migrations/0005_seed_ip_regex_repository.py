from __future__ import annotations

# -*- coding: utf-8 -*-

from django.db import migrations


IP_REGEX_SCRIPT = '''import ipaddress
import re
import sre_parse
from typing import Any, List, Sequence, Tuple

MAX_REVERSE_RESULTS = 2000


class RegexConversionError(Exception):
    """Regex parse failure."""


class RegexTooComplexError(RegexConversionError):
    """Too many reverse results."""


def _merge_unique(target: List[str], additions: Sequence[str], limit: int) -> List[str]:
    seen = set(target)
    for item in additions:
        if item not in seen:
            if len(target) >= limit:
                raise RegexTooComplexError(f"反推结果数量超过限制 {limit}")
            target.append(item)
            seen.add(item)
    return target


def _combine_segments(prefixes: List[str], suffixes: Sequence[str], limit: int) -> List[str]:
    if not suffixes:
        return prefixes

    combined: List[str] = []
    for prefix in prefixes:
        for suffix in suffixes:
            combined.append(prefix + suffix)
            if len(combined) > limit:
                raise RegexTooComplexError(f"反推结果数量超过限制 {limit}")

    ordered: List[str] = []
    seen = set()
    for item in combined:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def _expand_tokens(tokens: List[Tuple[int, Any]], limit: int) -> List[str]:
    results = ['']

    for token_type, value in tokens:
        if token_type == sre_parse.LITERAL:
            results = _combine_segments(results, [chr(value)], limit)

        elif token_type == sre_parse.IN:
            choices: List[str] = []
            for inner_type, inner_value in value:
                if inner_type == sre_parse.LITERAL:
                    choices.append(chr(inner_value))
                elif inner_type == sre_parse.RANGE:
                    start, end = inner_value
                    range_chars = [chr(code) for code in range(start, end + 1)]
                    choices = _merge_unique(choices, range_chars, limit)
                else:
                    raise RegexConversionError(f"不支持的字符集标记: {inner_type}")
            results = _combine_segments(results, choices, limit)

        elif token_type == sre_parse.BRANCH:
            branch_choices: List[str] = []
            _, branches = value
            for branch in branches:
                branch_tokens = branch.data if hasattr(branch, 'data') else branch
                branch_results = _expand_tokens(branch_tokens, limit)
                branch_choices = _merge_unique(branch_choices, branch_results, limit)
            results = _combine_segments(results, branch_choices, limit)

        elif token_type == sre_parse.SUBPATTERN:
            subpattern = value[-1]
            sub_tokens = subpattern.data if hasattr(subpattern, 'data') else subpattern
            sub_results = _expand_tokens(sub_tokens, limit)
            results = _combine_segments(results, sub_results, limit)

        elif token_type in (sre_parse.MAX_REPEAT, sre_parse.MIN_REPEAT):
            raise RegexConversionError("当前工具不支持包含重复量词的正则表达式")

        elif token_type == sre_parse.ASSERT:
            raise RegexConversionError("当前工具不支持包含断言的正则表达式")

        else:
            raise RegexConversionError(f"不支持的正则标记类型: {token_type}")

    return results


def regex_to_ips(pattern: str, max_results: int = MAX_REVERSE_RESULTS) -> List[str]:
    if not pattern:
        return []

    try:
        parsed = sre_parse.parse(pattern)
    except re.error as exc:
        raise RegexConversionError(f"正则表达式无效: {exc}") from exc

    raw_strings = _expand_tokens(parsed.data, max_results)

    ips: List[str] = []
    seen = set()
    for candidate in raw_strings:
        if candidate in seen:
            continue
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            continue
        seen.add(candidate)
        ips.append(candidate)
        if len(ips) > max_results:
            raise RegexTooComplexError(f"解析的IP数量超过限制 {max_results}")

    ips.sort(key=lambda ip: tuple(int(part) for part in ip.split('.')))
    return ips


def ip_to_regex(ip_list: Sequence[str]) -> Tuple[str, List[str]]:
    valid_ips: List[str] = []
    invalid_ips: List[str] = []

    for ip in ip_list:
        ip = ip.strip()
        if not ip:
            continue
        try:
            ipaddress.ip_address(ip)
            valid_ips.append(ip)
        except ValueError:
            invalid_ips.append(ip)

    if not valid_ips:
        return "", invalid_ips

    a_groups: dict[str, dict[str, dict[str, set[str]]]] = {}
    for ip in valid_ips:
        parts = ip.split('.')
        a_groups.setdefault(parts[0], {}).setdefault(parts[1], {}).setdefault(parts[2], set()).add(parts[3])

    main_patterns: List[str] = []

    for a_octet, b_octets_dict in a_groups.items():
        structure_groups: dict[Tuple[Any, ...], dict[str, Any]] = {}

        for b_octet, c_octets_dict in b_octets_dict.items():
            c_patterns = []
            c_signature = []

            for c_octet in sorted(c_octets_dict.keys(), key=lambda value: int(value)):
                d_octets = c_octets_dict[c_octet]
                d_patterns = process_last_octets(d_octets)
                d_expression = _combine_pattern_list(d_patterns)

                c_patterns.append(f"{c_octet}\\.{d_expression}")
                c_signature.append((c_octet, tuple(d_patterns)))

            cd_expression = _combine_pattern_list(c_patterns)
            cd_signature = tuple(c_signature)

            structure_groups.setdefault(cd_signature, {"expression": cd_expression, "b_values": set()})
            structure_groups[cd_signature]["b_values"].add(b_octet)

        a_patterns = []
        for group in sorted(structure_groups.values(), key=lambda item: min(int(v) for v in item["b_values"])):
            b_patterns = process_last_octets(group["b_values"])
            b_expression = _combine_pattern_list(b_patterns)
            a_patterns.append(f"{b_expression}\\.{group['expression']}")

        a_expression = _combine_pattern_list(a_patterns)
        main_patterns.append(f"({a_octet}\\.{a_expression})")

    result = '|'.join(main_patterns)
    return result, invalid_ips


def _combine_pattern_list(patterns: Sequence[str]) -> str:
    if not patterns:
        raise ValueError("模式列表不能为空")

    if len(patterns) == 1:
        return patterns[0]

    return f"({('|').join(patterns)})"


def process_last_octets(last_octets: Sequence[str]) -> List[str]:
    last_octets_list = sorted([int(x) for x in last_octets])
    patterns: List[str] = []

    if len(last_octets_list) == 2 and last_octets_list[1] == last_octets_list[0] + 1:
        first = last_octets_list[0]
        second = last_octets_list[1]

        if first >= 100:
            if first // 10 == second // 10:
                tens_hundreds = first // 10
                patterns.append(f"{tens_hundreds}[{first % 10}-{second % 10}]")
                return patterns
            patterns.append(f"({first}|{second})")
            return patterns

        if 10 <= first < 100:
            if first // 10 == second // 10:
                tens = first // 10
                patterns.append(f"{tens}[{first % 10}-{second % 10}]")
                return patterns
            patterns.append(f"({first}|{second})")
            return patterns

        patterns.append(create_range_pattern(first, second))
        return patterns

    if len(last_octets_list) > 1:
        by_hundreds: dict[int, List[int]] = {}
        by_tens: dict[int, List[int]] = {}
        units: List[int] = []

        for num in last_octets_list:
            if num >= 100:
                prefix = num // 10
                by_hundreds.setdefault(prefix, []).append(num % 10)
            elif num >= 10:
                tens = num // 10
                by_tens.setdefault(tens, []).append(num % 10)
            else:
                units.append(num)

        for prefix, digits in by_hundreds.items():
            digits.sort()
            ranges = _find_ranges(digits)
            range_parts = _build_range_parts(ranges)
            patterns.append(_format_prefix_range(prefix, range_parts))

        for tens, digits in by_tens.items():
            digits.sort()
            ranges = _find_ranges(digits)
            range_parts = _build_range_parts(ranges)
            patterns.append(_format_prefix_range(tens, range_parts))

        if units:
            units.sort()
            ranges = _find_ranges(units)
            for r in ranges:
                if len(r) >= 2:
                    patterns.append(create_range_pattern(r[0], r[-1]))
                else:
                    patterns.extend([str(n) for n in r])
    else:
        patterns.append(str(last_octets_list[0]))

    return patterns


def _find_ranges(digits: Sequence[int]) -> List[List[int]]:
    ranges: List[List[int]] = []
    current: List[int] = []
    for digit in digits:
        if not current or digit == current[-1] + 1:
            current.append(digit)
        else:
            ranges.append(current)
            current = [digit]
    if current:
        ranges.append(current)
    return ranges


def _build_range_parts(ranges: Sequence[Sequence[int]]) -> List[str]:
    parts: List[str] = []
    for r in ranges:
        if len(r) >= 2:
            pattern = create_range_pattern(r[0], r[-1])
            if pattern.startswith('[') and pattern.endswith(']'):
                parts.append(pattern[1:-1])
            else:
                parts.append(pattern)
        else:
            parts.extend(str(n) for n in r)
    return parts


def _format_prefix_range(prefix: int, range_parts: Sequence[str]) -> str:
    prefix_str = str(prefix)
    if len(range_parts) == 1:
        part = range_parts[0]
        if part.startswith('(') and part.endswith(')'):
            return f"{prefix_str}{part}"
        if '-' in part:
            return f"{prefix_str}[{part}]"
        return f"{prefix_str}{part}"
    return f"{prefix_str}[{('|').join(range_parts)}]"


def should_use_pipe_notation(start_num: int, end_num: int) -> bool:
    if len(str(start_num)) != len(str(end_num)):
        return True
    if start_num // 10 != end_num // 10:
        return True
    if end_num - start_num > 10:
        return True
    return False


def create_range_pattern(start_num: int, end_num: int) -> str:
    if should_use_pipe_notation(start_num, end_num):
        nums = [str(num) for num in range(start_num, end_num + 1)]
        return f"({('|').join(nums)})"
    return f"[{start_num}-{end_num}]"
'''


def seed_ip_regex_repository(apps, schema_editor):
    CodeDirectory = apps.get_model("tools", "CodeDirectory")
    CodeRepository = apps.get_model("tools", "CodeRepository")
    CodeRepositoryVersion = apps.get_model("tools", "CodeRepositoryVersion")

    directory, _ = CodeDirectory.objects.get_or_create(
        key="network-utilities",
        defaults={
            "title": "网络工具",
            "description": "内置网络脚本",
            "keywords": ["ip", "regex"],
            "builtin": True,
        },
    )

    repository, created = CodeRepository.objects.get_or_create(
        name="IP 正则助手",
        defaults={
            "language": "python",
            "tags": ["ip", "regex"],
            "description": "IP 与正则表达式互转脚本，可在代码管理中维护。",
            "directory": directory,
            "content": IP_REGEX_SCRIPT,
        },
    )

    if repository.latest_version is None:
        version = CodeRepositoryVersion.objects.create(
            repository=repository,
            version="v1.0.0",
            summary="初始化 IP 正则脚本",
            change_log="自动创建",
            content=IP_REGEX_SCRIPT,
        )
        repository.latest_version = version
        repository.content = version.content
        repository.save(update_fields=["latest_version", "content"])
    elif created is False and repository.content != repository.latest_version.content:
        repository.content = repository.latest_version.content
        repository.save(update_fields=["content"])


def remove_ip_regex_repository(apps, schema_editor):
    CodeDirectory = apps.get_model("tools", "CodeDirectory")
    CodeRepository = apps.get_model("tools", "CodeRepository")

    repo = CodeRepository.objects.filter(name="IP 正则助手").first()
    if repo:
        repo.delete()

    directory = CodeDirectory.objects.filter(key="network-utilities", builtin=True).first()
    if directory and not directory.repositories.exists():
        directory.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0004_alter_codedirectory_options_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_ip_regex_repository, remove_ip_regex_repository),
    ]
