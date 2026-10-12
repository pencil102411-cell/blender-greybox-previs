# -*- coding: utf-8 -*-
"""把本技能安装到各个 Agent 的技能目录。

  python -B install.py                 自动装到已存在的 ~/.claude/skills 和 ~/.codex/skills
  python -B install.py --claude        只装 Claude Code
  python -B install.py --codex         只装 Codex
  python -B install.py --dest <目录>   装到指定的技能目录（其他 Agent）
  python -B install.py --skip-setup    不运行环境检查

  python -B install.py --codex-mcp <mcp-for-blender 可执行文件路径>
      另外在 ~/.codex/config.toml 里登记 Blender MCP（已登记过就跳过）

同名旧版本会被替换。项目数据不在技能目录里，替换不会丢项目。
"""
import argparse, os, shutil, subprocess, sys

NAME = "blender-greybox-previs"
SRC = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".git", ".DS_Store")


def install_to(skills_dir):
    os.makedirs(skills_dir, exist_ok=True)
    dst = os.path.join(skills_dir, NAME)
    if os.path.abspath(dst) == SRC:
        print(f"  跳过（就是源目录）：{dst}")
        return dst
    if os.path.exists(dst):
        shutil.rmtree(dst)
        print(f"  已移除旧版本：{dst}")
    shutil.copytree(SRC, dst, ignore=IGNORE)
    print(f"  已安装：{dst}")
    return dst


def codex_mcp(cmd_path):
    cfg = os.path.join(HOME, ".codex", "config.toml")
    if not os.path.isfile(cmd_path):
        print(f"  MCP 可执行文件不存在：{cmd_path}")
        return
    text = open(cfg, "r", encoding="utf-8").read() if os.path.exists(cfg) else ""
    if "[mcp_servers.blender]" in text:
        print("  Codex 已登记过 Blender MCP，跳过")
        return
    if text:
        shutil.copy2(cfg, cfg + ".bak-before-blender-mcp")
    # TOML 单引号字符串不转义反斜杠，Windows 路径可以原样写
    block = ("\n[mcp_servers.blender]\n"
             f"command = '{cmd_path}'\n"
             "args = []\n"
             "startup_timeout_sec = 30\n")
    with open(cfg, "a", encoding="utf-8") as f:
        f.write(block)
    print(f"  已在 {cfg} 登记 Blender MCP（原文件备份为 config.toml.bak-before-blender-mcp）")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--claude", action="store_true")
    p.add_argument("--codex", action="store_true")
    p.add_argument("--dest", action="append", default=[])
    p.add_argument("--skip-setup", action="store_true")
    p.add_argument("--codex-mcp", metavar="MCP_EXE")
    a = p.parse_args()

    targets = list(a.dest)
    if a.claude:
        targets.append(os.path.join(HOME, ".claude", "skills"))
    if a.codex:
        targets.append(os.path.join(HOME, ".codex", "skills"))
    if not targets and not a.codex_mcp:
        for agent in (".claude", ".codex"):
            if os.path.isdir(os.path.join(HOME, agent)):
                targets.append(os.path.join(HOME, agent, "skills"))
    if not targets and not a.codex_mcp:
        print("没找到 ~/.claude 或 ~/.codex。用 --dest <技能目录> 指定安装位置。")
        sys.exit(1)

    print("安装技能：")
    installed = [install_to(t) for t in targets]
    if a.codex_mcp:
        print("登记 Codex MCP：")
        codex_mcp(a.codex_mcp)
    if installed and not a.skip_setup:
        print("\n检查运行环境：", flush=True)
        r = subprocess.run([sys.executable, "-B", os.path.join(installed[0], "scripts", "previs.py"), "setup"])
        if r.returncode != 0:
            print("\n环境检查没通过，按上面的提示处理后，再运行：")
            print(f'  python -B "{os.path.join(installed[0], "scripts", "previs.py")}" setup')
    print("\n完成。新开一个 Agent 对话，说「用灰模预演」或「按平面图做个预演视频」就会用到这个技能。")


if __name__ == "__main__":
    main()
