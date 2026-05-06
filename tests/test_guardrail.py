"""Quick smoke test: verify guardrail directly without making LLM API calls."""
import json
import re
import sys
from pathlib import Path

root = Path(__file__).parent.parent
questions_path = root / "configs" / "questions.json"

# Replicate the same patterns from cli.py
_BLOCKED_PATTERNS: list[re.Pattern] = [re.compile(p, re.IGNORECASE) for p in [
    r"\b(bomb|explosive|detonate|bioweapon|chemical\s+weapon|nerve\s+agent|anthrax|ricin|sarin)\b",
    r"\b(vũ khí|chất nổ|bom|kích nổ|vũ khí sinh học|vũ khí hóa học|chất độc thần kinh)\b",
    r"\b(hack|exploit|malware|ransomware|ddos|sql\s*injection|zero.?day|botnet|keylogger|rootkit)\b",
    r"\b(tấn công mạng|phần mềm độc hại|khai thác lỗ hổng|đánh cắp dữ liệu)\b",
    r"\b(synthesize\s+drug|make\s+(meth|heroin|cocaine|fentanyl)|drug\s+lab)\b",
    r"\b(tổng hợp ma túy|sản xuất ma túy|chế\s+ma túy|methamphetamine)\b",
    r"\b(child\s+(porn|sexual|abuse\s+material)|csam|underage\s+(nude|sex))\b",
    r"\b(khiêu dâm trẻ em|xâm hại tình dục trẻ em)\b",
    r"\b(how\s+to\s+kill|how\s+to\s+murder|assassination\s+plan|terrorist\s+attack|genocide)\b",
    r"\b(cách giết người|âm mưu ám sát|tấn công khủng bố|diệt chủng)\b",
    r"\b(fake\s+(passport|id|visa|degree|certificate)|counterfeit\s+money|money\s+laundering)\b",
    r"\b(làm giả hộ chiếu|làm giả chứng chỉ|rửa tiền|tiền giả)\b",
]]

def is_blocked(query: str) -> bool:
    return any(p.search(query) for p in _BLOCKED_PATTERNS)

with open(questions_path, encoding="utf-8") as f:
    questions = json.load(f)["questions"]

passed = 0
for q in questions:
    blocked = is_blocked(q["query"])
    expected = q["expect_blocked"]
    ok = blocked == expected
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    reason = f" [{q.get('block_reason', '')}]" if expected else ""
    label = q["query"][:55]
    print(f"[{status}] #{q['id']:02d} blocked={str(blocked):<5} expected={str(expected):<5} |{reason} {label}")

print(f"\nResult: {passed}/{len(questions)} passed")
sys.exit(0 if passed == len(questions) else 1)
