# sync_pack.py
"""
Albion Beacon — GitHub ↔ GPT 협업 동기화 패키저
- 목적:
  1) 리포지토리 최신화(clone/pull, main 브랜치)
  2) docs/_sync/ 에 협업 번들 생성:
     - tree.txt           : 폴더/파일 구조(최대 3단계)
     - commits.md         : 최근 커밋(최대 20개)
     - changes.txt        : 변경 파일 목록(name-status)
     - changes.patch      : 변경 패치(unified diff)
     - paste_for_gpt.md   : GPT에게 그대로 붙여넣는 요약 패키지

- 기본 기준:
  - BRANCH = "main"
  - BASEREF = "origin/main"   # main을 기준으로 비교
  - MAX_EMBED_LINES = 400     # 이 줄 수 이하의 작은 파일은 '전체 본문'을 paste_for_gpt.md에 포함
"""

import os
import subprocess
import textwrap
import pathlib
import sys
from typing import List

# ===== 설정 (환경변수로 덮어쓰기 가능) =====
REPO_URL = os.getenv("REPO_URL", "https://github.com/dalyn98/Albion_Beacon")
REPO_DIR = os.getenv("REPO_DIR", "./Albion_Beacon")
BRANCH   = os.getenv("BRANCH", "main")
BASEREF  = os.getenv("BASEREF", "origin/main")  # ← 사용자가 요청한 'main 기준'
MAX_EMBED_LINES = int(os.getenv("MAX_EMBED_LINES", "400"))  # 이 줄 수 이하 파일은 전체 포함

# ===== 유틸 =====
def run(cmd: str, cwd: str | None = None) -> str:
    """쉘 명령 실행(에러 시 예외). 표준출력 반환."""
    res = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"[cmd failed] {cmd}\nSTDERR:\n{res.stderr}")
    return res.stdout.strip()

def ensure_git():
    try:
        run("git --version")
    except Exception as e:
        raise RuntimeError("Git이 설치되어 있어야 합니다: https://git-scm.com/") from e

def ensure_repo():
    if not os.path.exists(REPO_DIR):
        print(f"[clone] {REPO_URL} -> {REPO_DIR}")
        run(f"git clone {REPO_URL} {REPO_DIR}")
    print("[fetch] tags & all remotes")
    run("git fetch --all --tags", cwd=REPO_DIR)
    print(f"[checkout] {BRANCH}")
    run(f"git checkout {BRANCH}", cwd=REPO_DIR)
    print("[pull] --ff-only")
    run("git pull --ff-only", cwd=REPO_DIR)

def make_sync_dir() -> str:
    sync_dir = os.path.join(REPO_DIR, "docs", "_sync")
    os.makedirs(sync_dir, exist_ok=True)
    return sync_dir

def capture_tree(repo_dir: str, sync_dir: str) -> str:
    out_path = os.path.join(sync_dir, "tree.txt")
    try:
        if os.name == "nt":
            txt = run("cmd /c tree /F", cwd=repo_dir)
        else:
            try:
                txt = run("tree -L 3", cwd=repo_dir)
            except Exception:
                txt = run("find . -maxdepth 3 -print", cwd=repo_dir)
    except Exception:
        txt = "(tree 생성 실패)"
    pathlib.Path(out_path).write_text(txt, encoding="utf-8")
    return txt

def capture_commits(repo_dir: str, sync_dir: str, n: int = 20) -> str:
    out_path = os.path.join(sync_dir, "commits.md")
    try:
        commits = run(f"git log --oneline -n {n}", cwd=repo_dir)
    except Exception:
        commits = "(커밋 로그 없음)"
    md = f"# Recent Commits (Top {n})\n```\n{commits}\n```\n"
    pathlib.Path(out_path).write_text(md, encoding="utf-8")
    return md

def capture_changes(repo_dir: str, sync_dir: str, base: str) -> str:
    out_path = os.path.join(sync_dir, "changes.txt")
    try:
        changes = run(f"git diff --name-status {base}..HEAD", cwd=repo_dir)
    except Exception:
        changes = ""
    pathlib.Path(out_path).write_text(changes, encoding="utf-8")
    return changes

def capture_patch(repo_dir: str, sync_dir: str, base: str) -> str:
    out_path = os.path.join(sync_dir, "changes.patch")
    targets = "src client server core config README.md docs"
    try:
        patch = run(f"git diff {base}..HEAD -- {targets}", cwd=repo_dir)
    except Exception:
        patch = ""
    pathlib.Path(out_path).write_text(patch, encoding="utf-8")
    return patch

def list_changed_files(repo_dir: str, base: str) -> List[str]:
    try:
        out = run(f"git diff --name-only {base}..HEAD", cwd=repo_dir)
    except Exception:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]

def embed_small_files(repo_dir: str, files: List[str], max_lines: int) -> str:
    """작은 파일(라인 수 ≤ max_lines)은 전체 내용을 마크다운 코드블록으로 반환."""
    blocks = []
    for rel in files:
        path = os.path.join(repo_dir, rel)
        if not os.path.exists(path) or not os.path.isfile(path):
            continue
        try:
            text = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        lines = text.count("\n") + 1
        if lines <= max_lines:
            lang = pathlib.Path(rel).suffix.lstrip(".") or "txt"
            block = f"### File: {rel} (lines: {lines})\n```{lang}\n{text}\n```\n"
            blocks.append(block)
    return "\n".join(blocks) if blocks else "변경된 소형 파일 없음.\n"

def build_paste_md(sync_dir: str, tree_txt: str, commits_md: str, changes_txt: str,
                   base: str, small_files_md: str) -> None:
    out_path = os.path.join(sync_dir, "paste_for_gpt.md")
    preamble = textwrap.dedent(f"""
    # Albion Beacon — Sync Bundle

    이 문서는 GPT 협업용 붙여넣기 패키지입니다. 아래 순서대로 공유하세요.

    ## 1) 폴더 트리
    ```
    {tree_txt}
    ```

    ## 2) 최근 커밋(Top 20)
    {commits_md}

    ## 3) 변경 파일 목록 (base: {base})
    ```
    {changes_txt}
    ```

    ## 4) 작은 변경 파일의 전체 본문
    """).strip("\n")
    tail = textwrap.dedent("""
    ## 5) 큰 변경은 패치로 확인
    - 자세한 변경은 `docs/_sync/changes.patch` 참조

    ## 6) 지시사항
    - 위 '붙여넣기 패키지' 전체를 GPT에게 전달
    - 필요한 경우 `changes.patch`에서 특정 파일의 diff 일부를 추가로 첨부
    """).strip("\n")

    content = f"{preamble}\n\n{small_files_md}\n\n{tail}\n"
    pathlib.Path(out_path).write_text(content, encoding="utf-8")

def main():
    print("[check] git")
    ensure_git()

    print("[repo] ensure clone/pull")
    ensure_repo()

    sync_dir = make_sync_dir()

    print("[tree] capture")
    tree_txt = capture_tree(REPO_DIR, sync_dir)

    print("[commits] capture")
    commits_md = capture_commits(REPO_DIR, sync_dir, n=20)

    base = BASEREF
    print(f"[base] 비교 기준: {base}")

    print("[changes] list")
    changes_txt = capture_changes(REPO_DIR, sync_dir, base=base)

    print("[patch] diff")
    _ = capture_patch(REPO_DIR, sync_dir, base=base)

    print("[embed] small files")
    changed_files = list_changed_files(REPO_DIR, base=base)
    small_files_md = embed_small_files(REPO_DIR, changed_files, MAX_EMBED_LINES)

    print("[bundle] paste_for_gpt.md")
    build_paste_md(sync_dir, tree_txt, commits_md, changes_txt, base, small_files_md)

    print("\n[완료] docs/_sync/ 폴더에 번들이 생성됨.")
    print(" - docs/_sync/paste_for_gpt.md  ← 이 파일을 나에게 그대로 붙여넣기")
    print(" - docs/_sync/changes.patch     ← 큰 변경(diff) 참고")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[에러] {e}", file=sys.stderr)
        sys.exit(1)
