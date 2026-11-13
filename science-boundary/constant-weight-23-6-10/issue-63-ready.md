### 问题 · Problem

**中文：** 构造尽可能大的二进制常重量码 A(23,6,10)。每个码字是长度 23、恰有 10 个 1 的二进制串，任意两个不同码字的汉明距离至少为 6。提交的证书只包含码字数据。

**English:** Construct the largest possible binary constant-weight code A(23,6,10): each codeword has length 23, Hamming weight 10 and pairwise minimum Hamming distance 6. The certificate contains only the codewords.

### 为什么重要 · Why it matters

**中文：** 常重量码是编码理论、组合设计和集合打包的经典对象。A(n,d,w) 有持续维护的专业纪录表；2026 年 Christian Lysenstøen 获得改进构造，Andries E. Brouwer 进一步优化并更新该表。刷新这项参数的构造下界是该领域公认的研究进展，而不只是排行榜名次。

**English:** Constant-weight codes are standard objects in coding theory, combinatorial designs and packing. A(n,d,w) is tracked by a long-running specialist record table. In 2026 Christian Lysenstøen produced new explicit constructions, which Andries E. Brouwer further polished and listed. Improving this constructive bound would be a meaningful coding-theory result.

### 进度指标与方向 · Metric and direction

**中文：** 参数固定为 n=23、d=6、w=10；得分为合法码字数量，精确整数，**越大越好**，绝对 ε=1。第一个突破目标为 2993。

**English:** Fix n=23, d=6, w=10. Score = number of valid codewords, an exact integer; **maximize**, with absolute epsilon = 1. First breakthrough: a 2993-word code.

### 验证器思路 · Verifier

**中文：** certificate.json 是只有一个 codewords 字段的 JSON 对象，值为表示 23 位码字的整数数组。Python 3.12 标准库验证器检查每个整数的取值范围、恰好 10 个 1、互异性和所有码字对的 XOR 位计数至少为 6。按数值排序并使用紧凑 JSON 编码求 SHA-256。无需网络、第三方库、SAT 或浮点容差。

**English:** certificate.json is a JSON object with exactly one codewords field holding integer-encoded 23-bit words. The Python 3.12 standard-library-only verifier checks integer range, weight 10, distinctness, and XOR bit count >=6 for each pair. Sorted compact JSON determines the canonical SHA-256. No network, external solver or floating point is used.

### 预设基线 · Baseline

**中文：** [Brouwer 在线表](https://aeb.win.tue.nl/codes/Andw.html)给出构造下界 2992、理论上界 7521。[原始 2992 码字文件](https://aeb.win.tue.nl/codes/cwc/d6/a23.6.10.2992H) 是十六进制整数文本，首行为 $BASE=16。已重建为[可直接提交的 JSON 证书](https://github.com/teddyli18000/web-ingest/blob/main/science-boundary/constant-weight-23-6-10/baseline/certificate.json)，并公开[复现程序](https://github.com/teddyli18000/web-ingest/blob/main/science-boundary/constant-weight-23-6-10/code/reproduce_baseline.py)。

**English:** [Brouwer's live table](https://aeb.win.tue.nl/codes/Andw.html) gives a 2992-word construction and upper bound 7521. The [original hex word list](https://aeb.win.tue.nl/codes/cwc/d6/a23.6.10.2992H) begins with $BASE=16. The witness has been independently reconstructed into a [submission-ready JSON certificate](https://github.com/teddyli18000/web-ingest/blob/main/science-boundary/constant-weight-23-6-10/baseline/certificate.json), with the [reproducer](https://github.com/teddyli18000/web-ingest/blob/main/science-boundary/constant-weight-23-6-10/code/reproduce_baseline.py) provided.

### 为什么还有余量 · Headroom

**中文：** 已知构造 2992 严格小于记录的上界 7521；该差距不保证可达，但 2026 年从 2979 到 2992 的实际改进表明这是仍在发展的建设性问题。任何至少 2993 个码字的合法证书均可改进现有下界。

**English:** The published witness 2992 is strictly below the table's 7521 upper bound. This gap is not a promise of attainability, but the successive 2026 improvements from 2979 to 2992 demonstrate active constructive work. Any valid witness with 2993 or more codewords improves the record.

### 数据与许可 · Data and licence

**中文：** 2992 个整数码字来源于 [Brouwer 维护的公开构造文件](https://aeb.win.tue.nl/codes/cwc/d6/a23.6.10.2992H)，通过解析十六进制数、转换整数、排序及 JSON 序列化重建，不复制原始网页的文字表达。完整文件和 JSON 转写的**明确再发布授权条款目前尚未找到公开可核验的依据**；此处不主张已获 CC0、CC BY 或其他授权，也不将第三方数据重新许可为 CC0。原作者及数据提供者的权利保留，待补可核验授权依据。致谢 Christian Lysenstøen 的 2026 年构造进展，以及 Andries E. Brouwer 的纪录表维护与进一步优化。详见 [原始数据](https://aeb.win.tue.nl/codes/cwc/d6/a23.6.10.2992H)、[纪录表](https://aeb.win.tue.nl/codes/Andw.html)、[Lysenstøen 论文](https://arxiv.org/abs/2607.19550)。该证书不含个人数据。

**English:** The 2992 numerical codewords come from [Brouwer's published witness](https://aeb.win.tue.nl/codes/cwc/d6/a23.6.10.2992H), reconstructed by hexadecimal decoding, integer conversion, sorting and JSON encoding without reproducing the source page's prose. An **independently verifiable explicit redistribution authorization for the full list and its JSON transcription is not yet identified**; we do not assert CC0, CC BY, or other permission, and do not relicense the third-party baseline. Attribution and rights are reserved pending verified permission evidence. Credit Christian Lysenstøen's 2026 contribution and Andries E. Brouwer's maintained records and subsequent polishing. Sources: [original data](https://aeb.win.tue.nl/codes/cwc/d6/a23.6.10.2992H), [table](https://aeb.win.tue.nl/codes/Andw.html), [research paper](https://arxiv.org/abs/2607.19550). No personal data is present.

### 智能体初查 · Agent check

| Criterion | Evidence |
| --- | --- |
| Useful or influential | Standard coding-theory quantity in a long-running public record table and a 2026 research paper. |
| Verifiable progress | Any valid 2993-word witness strictly improves the recorded constructive lower bound. |
| Precisely defined | Fixed n=23, d=6, w=10; exact integer count; maximize; absolute epsilon = 1. |
| Published record | The 2992-word source is linked directly from Brouwer's table and reproduced as JSON. |
| Exactly checkable | Pure Python 3.12, exhaustive pairwise bit arithmetic in well under one second. |
| Data and licence | Public mathematical data with source attribution; explicit permission for redistribution of the full 2992-word list is pending independently verifiable evidence. |
| Not a repeat | No duplicate among the published Few Shots p001–p017 or searched proposal Issues. |

**实测 / Verified results (Python 3.12.16):** 2992 distinct weight-10 codewords, exact minimum distance **6** over **4,474,536** pairs. The independent 8-subset test found **134,640** unique 8-subsets. The baseline passes the draft verifier; one distance-2 counterexample and one invalid-format JSON certificate are both rejected. Four unit tests passed. All computations are documented in [the successful GitHub Actions run](https://github.com/teddyli18000/web-ingest/actions/runs/43370484174) and [baseline-check.json](https://github.com/teddyli18000/web-ingest/blob/main/science-boundary/constant-weight-23-6-10/results/baseline-check.json).

**Baseline output / 基线验证：**
```json
{"valid":true,"score":"2992","canonical_hash":"6451ae0eb1887314ef32dea943da4ed879f2d7c440115980708e56cf0c4ed9c4","message":"ok"}
```

**Broken-distance output / 距离破坏：**
```json
{"valid":false,"score":null,"canonical_hash":null,"message":"invalid certificate"}
```

**Wrong-format output / 格式错误：**
```json
{"valid":false,"score":null,"canonical_hash":null,"message":"invalid certificate"}
```

**Timing / 耗时：** verifier 0.144648 s; independent subset check 0.078614 s.

**Source SHA-256:** 5e1f5aa477db162cc46705b4135dbd48878d0640c73492ec63615d1305f0d934

**Certificate SHA-256:** 82a17001b56ad46b6fbef42c2b8059052d59a1c90bbe188308e6ccd1205974d5

**Canonical SHA-256:** 6451ae0eb1887314ef32dea943da4ed879f2d7c440115980708e56cf0c4ed9c4

<details><summary>verify.py (Python 3.12, standard library only)</summary>

```python
#!/usr/bin/env python3
"""Few Shots draft verifier for binary constant-weight A(23,6,10)."""

import hashlib
import json
import os
import stat
import sys
from pathlib import Path

N = 23
WEIGHT = 10
MIN_DISTANCE = 6
MAX_WORDS = 10000
MAX_BYTES = 100000
MAX_DEPTH = 2
MAX_INT_DIGITS = 12


class Invalid(Exception):
    pass


def check_depth(text):
    depth = 0
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise Invalid("JSON nesting exceeds limit")
        elif char in "]}":
            depth -= 1
    # The JSON decoder validates matching brackets and strings.


def reject_token(_):
    raise Invalid("noninteger numeric token")


def bounded_int(token):
    if len(token.lstrip("-")) > MAX_INT_DIGITS:
        raise Invalid("integer token exceeds limit")
    return int(token)


def unique_keys(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise Invalid("duplicate JSON key")
        result[name] = value
    return result


def read_certificate(shot_dir):
    path = Path(shot_dir) / "certificate.json"
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise Invalid("certificate is not a regular file")
        with os.fdopen(fd, "rb", closefd=False) as handle:
            data = handle.read(MAX_BYTES + 1)
    finally:
        os.close(fd)
    if len(data) > MAX_BYTES:
        raise Invalid("certificate exceeds byte limit")
    return data


def parse_certificate(data):
    text = data.decode("utf-8")
    check_depth(text)
    return json.loads(text, parse_int=bounded_int, parse_float=reject_token,
                      parse_constant=reject_token, object_pairs_hook=unique_keys)


def check(certificate):
    if type(certificate) is not dict or set(certificate) != {"codewords"}:
        raise Invalid("expected a single codewords field")
    words = certificate["codewords"]
    if type(words) is not list or not (1 <= len(words) <= MAX_WORDS):
        raise Invalid("codewords must be a nonempty bounded list")
    for word in words:
        if type(word) is not int or not (0 <= word < (1 << N)) or word.bit_count() != WEIGHT:
            raise Invalid("invalid 23-bit weight-10 codeword")
    if len(set(words)) != len(words):
        raise Invalid("duplicate codewords")
    for i, word in enumerate(words):
        for prior in words[:i]:
            if (word ^ prior).bit_count() < MIN_DISTANCE:
                raise Invalid("minimum distance below 6")
    canonical = json.dumps({"codewords": sorted(words)}, separators=(",", ":"))
    return {"valid": True, "score": str(len(words)),
            "canonical_hash": hashlib.sha256(canonical.encode("ascii")).hexdigest(),
            "message": "ok"}


def verify(shot_dir):
    try:
        certificate = parse_certificate(read_certificate(shot_dir))
        return check(certificate)
    except (OSError, UnicodeError, ValueError, Invalid, RecursionError):
        return {"valid": False, "score": None, "canonical_hash": None,
                "message": "invalid certificate"}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 verify.py <shot_dir>")
    print(json.dumps(verify(sys.argv[1]), separators=(",", ":")))
```
</details>

The above verifier is a draft. If accepted, Few Shots referees write and review the official verifier.

### 确认 · Confirm

- [x] 参与者只需提交数据（证书），验证器不需要运行参与者的代码。 · Participants submit only data (a certificate); the verifier never runs their code.
- [x] 我有权公开以上内容，所列数据的许可允许公开使用。 · I may publish the above, and the data's licence allows public use.
- [x] 我理解题目如被采用，会对所有人同时公开，出题人也不会提前拿到题面、验证器或基线。 · I understand that an accepted problem is published to everyone at once, with no early access for the proposer.
