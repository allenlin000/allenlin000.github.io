import os
import re
import sys


def check_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    filename = os.path.basename(filepath)
    violations = []

    # --------------------------------------------------
    # 1. 禁用標點
    # --------------------------------------------------
    punctuation_checks = [
        (r'—', 'Em-dash', '改用句號或逗號'),
        (r'；', 'Semicolon', '改用句號或逗號'),
    ]

    for i, line in enumerate(lines):
        for pattern, type_name, suggestion in punctuation_checks:
            if re.search(pattern, line):
                violations.append({
                    'line': i + 1,
                    'type': f'禁用標點 ({type_name})',
                    'content': line.strip(),
                    'suggestion': suggestion
                })

    # --------------------------------------------------
    # 2. 禁用句型
    # --------------------------------------------------
    sentence_patterns = [
        (r'不是.*?而是.*?', '不是...而是...', '改用直述句'),
        (r'在.*?的時代', '在...的時代', '刪除或改寫'),
        (r'不只.*?還是.*?', '不只...還是...', '改用直述句'),
        (r'不只是.*?而是.*?', '不只是...而是...', '改用直述句'),
        (r'不需要.*?只需要', '不需要...只需要', '改用直述句'),
    ]

    for i, line in enumerate(lines):
        for pattern, type_name, suggestion in sentence_patterns:
            if re.search(pattern, line):
                violations.append({
                    'line': i + 1,
                    'type': f'禁用句型 ({type_name})',
                    'content': line.strip(),
                    'suggestion': suggestion
                })

    # --------------------------------------------------
    # 3. 禁用詞彙
    # --------------------------------------------------
    banned_words = [
        ('賦能', '賦能', '換個詞'),
        ('深度', '深度', '具體一點'),
        ('快速變化', '快速變化', '具體一點'),
        ('記住！', '記住！', '不要命令讀者'),
        ('一起撐', '一起撐', '太矯情'),
        ('溫柔', '溫柔', '太矯情'),
        ('陪你一起', '陪你一起', '太矯情'),
    ]

    for i, line in enumerate(lines):
        for word, type_name, suggestion in banned_words:
            if word in line:
                violations.append({
                    'line': i + 1,
                    'type': f'禁用詞彙 ({type_name})',
                    'content': line.strip(),
                    'suggestion': suggestion
                })

    # --------------------------------------------------
    # 4. 引號數量限制（全篇最多 1 個）
    # --------------------------------------------------
    chinese_quotes = content.count('「')
    english_quotes = content.count('"') // 2
    quote_count = chinese_quotes + english_quotes

    if quote_count > 1:
        violations.append({
            'line': 0,
            'type': '引號過多',
            'content': f'全篇共 {quote_count} 個引號',
            'suggestion': '一篇最多使用 1 個引號'
        })

    # --------------------------------------------------
    # 5. Hook 禁用模式（前 5 行非空白）
    # --------------------------------------------------
    hook_patterns = [
        (r'你一定會很驚訝', '假裝驚訝'),
        (r'說出來你可能不信', '假裝驚訝'),
        (r'非常重要', '過度強調'),
        (r'絕對不能錯過', '過度強調'),
        (r'一定要看到最後', '過度強調'),
        (r'我發現一件事', '空洞鋪陳'),
        (r'讓我告訴你一個秘密', '空洞鋪陳'),
        (r'是的，你沒看錯', '冗餘確認'),
        (r'沒錯，就是這樣', '冗餘確認'),
        (r'太棒了', '誇張情緒'),
        (r'天啊', '誇張情緒'),
        (r'超級重要', '誇張情緒'),
    ]

    non_empty_lines = []
    line_map = []

    for idx, line in enumerate(lines):
        if line.strip():
            non_empty_lines.append(line)
            line_map.append(idx + 1)

    for i, line in enumerate(non_empty_lines[:5]):
        for pattern, type_name in hook_patterns:
            if re.search(pattern, line):
                violations.append({
                    'line': line_map[i],
                    'type': f'Hook 禁用模式 ({type_name})',
                    'content': line.strip(),
                    'suggestion': '換個切入點'
                })

    return violations


def generate_report(target_dir):
    files = [
        f for f in os.listdir(target_dir)
        if f.endswith('.md') and f != 'INDEX.md'
    ]
    files.sort()

    print("## 批次 Review 彙總\n")
    print("| 檔案 | 狀態 | 違規數 |")
    print("|------|------|--------|")

    details = []

    for filename in files:
        filepath = os.path.join(target_dir, filename)
        violations = check_file(filepath)

        status = "✅ Pass"

        if violations:
            is_fail = False
            for v in violations:
                if (
                    '禁用句型' in v['type']
                    or '禁用詞彙' in v['type']
                    or 'Hook' in v['type']
                ):
                    is_fail = True
                    break

            if is_fail:
                status = "❌ Fail"
            else:
                status = "⚠️ Minor"

        print(f"| {filename} | {status} | {len(violations)} |")

        if violations:
            details.append(f"\n## Review 結果：{filename}\n")
            details.append("### ❌ 違規項目\n")
            details.append("| # | 位置 | 違規類型 | 原文 | 建議修正 |")
            details.append("|---|------|----------|------|----------|")

            for i, v in enumerate(violations):
                content_display = v['content']
                if len(content_display) > 20:
                    content_display = content_display[:20] + '...'

                line_str = str(v['line']) if v['line'] > 0 else "全文"
                details.append(
                    f"| {i + 1} | {line_str} | {v['type']} | "
                    f"`{content_display}` | {v['suggestion']} |"
                )

    print("\n" + "".join(details))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python review.py <文章資料夾路徑>")
        sys.exit(1)

    target_dir = sys.argv[1]
    generate_report(target_dir)
