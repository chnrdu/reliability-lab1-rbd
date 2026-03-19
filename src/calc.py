#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生版：读取 components.csv + mission_profile.csv + model.json
- 由 mission_profile 计算每个元件 duty
- 由 model.json 计算系统任务可靠度
- 生成 output/lab1_report_<student_id>_<name>.md
- 内置 sanity checks

用法：
python src/calc.py --student_id 2026XXXXXX --student_name zhangsan --N 60
"""

import csv
import json
import math
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Union, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
COMP_PATH = DATA_DIR / "components.csv"
PROFILE_PATH = DATA_DIR / "mission_profile.csv"
MODEL_PATH = DATA_DIR / "model.json"

EXPERIMENT_NAME = "实验：完整搬运循环任务可靠度评估（学生版：RBD+任务剖面）"

def R_exp(lmbda: float, t: float) -> float:
    return math.exp(-lmbda * t)

def R_parallel(Rs: List[float]) -> float:
    p_fail = 1.0
    for r in Rs:
        p_fail *= (1.0 - r)
    return 1.0 - p_fail

def R_series(Rs: List[float]) -> float:
    r = 1.0
    for x in Rs:
        r *= x
    return r

def load_components() -> Dict[str, Tuple[str,float]]:
    comps = {}
    with COMP_PATH.open("r", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        for row in rd:
            cid = row["id"].strip()
            name = row["name"].strip()
            lam = float(row["lambda_per_h"])
            comps[cid] = (name, lam)
    return comps

def load_profile(component_ids: List[str]) -> Tuple[float, Dict[str, float], List[Dict[str, Any]]]:
    """
    returns:
      t_cyc: 单循环时长（h）=五阶段时长之和
      duty_map: 每个元件 duty
      rows: profile 原始行（便于报告展示）
    """
    rows = []
    # sum working time per component
    work_time = {cid: 0.0 for cid in component_ids}
    t_cyc = 0.0

    with PROFILE_PATH.open("r", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        missing = [c for c in ["phase","duration_h"]+component_ids if c not in rd.fieldnames]
        if missing:
            raise ValueError(f"mission_profile.csv 缺少列：{missing}")
        for row in rd:
            phase = row["phase"].strip()
            dur = float(row["duration_h"])
            if dur <= 0:
                raise ValueError(f"阶段 {phase} 的 duration_h 必须>0")
            t_cyc += dur
            for cid in component_ids:
                flag = int(float(row[cid]))
                if flag not in (0,1):
                    raise ValueError(f"{phase} 阶段 {cid} 标记必须为0/1")
                if flag == 1:
                    work_time[cid] += dur
            rows.append({"phase": phase, "duration_h": dur, **{cid: int(float(row[cid])) for cid in component_ids}})

    if t_cyc <= 0:
        raise ValueError("t_cyc 计算得到 <=0，请检查 mission_profile.csv")

    duty = {cid: work_time[cid] / t_cyc for cid in component_ids}
    return t_cyc, duty, rows

Node = Union[str, Dict[str, Any]]

def parse_model() -> Node:
    data = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    model = data.get("model")
    if model == "__FILL__" or model is None:
        raise ValueError("data/model.json 仍为占位符 __FILL__，请先补全你的 RBD 结构。")
    return model

def eval_node(node: Node, R_map: Dict[str, float]) -> float:
    """递归计算 RBD 节点可靠度"""
    if isinstance(node, str):
        if node not in R_map:
            raise KeyError(f"模型中引用了未知元件：{node}")
        return R_map[node]
    if isinstance(node, dict):
        if "series" in node:
            return R_series([eval_node(x, R_map) for x in node["series"]])
        if "parallel" in node:
            return R_parallel([eval_node(x, R_map) for x in node["parallel"]])
        raise ValueError(f"不支持的节点类型：{node.keys()}（仅支持 series/parallel）")
    raise TypeError(f"非法节点：{type(node)}")

def strip_parallel(node: Node) -> Node:
    """用于sanity check：把并联节点退化为单支路（取第一个），其余保持"""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        if "series" in node:
            return {"series": [strip_parallel(x) for x in node["series"]]}
        if "parallel" in node:
            first = node["parallel"][0]
            return strip_parallel(first)
    return node

def main():
    import re
    ap = argparse.ArgumentParser()
    ap.add_argument("--student_id", required=True)
    ap.add_argument("--student_name", required=True)
    ap.add_argument("--N", type=int, default=60, help="班次循环次数")
    args = ap.parse_args()
    if args.N <= 0:
        raise ValueError("N 必须>0")
    # 统一命名规范
    safe_name = re.sub(r'[^\w\u4e00-\u9fa5]', '', str(args.student_name))
    OUT_PATH = REPO_ROOT / "output" / f"lab1_report_{args.student_id}_{safe_name}.md"

    comps = load_components()
    component_ids = sorted(comps.keys(), key=lambda x: int(x[1:]))  # C1..C19

    t_cyc, duty, profile_rows = load_profile(component_ids)
    T = args.N * t_cyc

    # 单元件：λ_eff=λ*duty；R(T)=exp(-λ_eff*T)
    lam_eff = {}
    R_map = {}
    for cid in component_ids:
        name, lam = comps[cid]
        lam_eff[cid] = lam * duty[cid]
        R_map[cid] = R_exp(lam_eff[cid], T)


    model = parse_model()

    # 检查所有元件都被RBD结构引用
    def collect_rbd_components(node):
        if isinstance(node, str):
            return {node}
        if isinstance(node, dict):
            if "series" in node:
                s = set()
                for x in node["series"]:
                    s |= collect_rbd_components(x)
                return s
            if "parallel" in node:
                s = set()
                for x in node["parallel"]:
                    s |= collect_rbd_components(x)
                return s
        return set()

    rbd_cids = collect_rbd_components(model)
    missing = [cid for cid in component_ids if cid not in rbd_cids]
    if missing:
        raise ValueError(f"RBD结构未包含所有元件，缺少: {missing}\n请检查model.json，确保所有元件都被引用。")

    R_sys = eval_node(model, R_map)

    # ---- sanity checks ----
    # 1) 去冗余应变差
    model_stripped = strip_parallel(model)
    R_sys_stripped = eval_node(model_stripped, R_map)
    check1_ok = (R_sys_stripped <= R_sys + 1e-12)

    # 2) 缩短任务时间应变好（T/2）
    R_map_half = {cid: R_exp(lam_eff[cid], T/2.0) for cid in component_ids}
    R_sys_half = eval_node(model, R_map_half)
    check2_ok = (R_sys_half >= R_sys - 1e-12)

    if not check1_ok or not check2_ok:
        raise RuntimeError(
            "Sanity check 未通过：\n"
            f"- 去冗余应变差：{check1_ok}（R_noRed={R_sys_stripped:.6f}, R={R_sys:.6f})\n"
            f"- 缩短任务时间应变好：{check2_ok}（R_halfT={R_sys_half:.6f}, R={R_sys:.6f})\n"
            "请检查 mission_profile.csv 与 model.json 的合理性（边界/并联/单位/占空比）。"
        )

    weak_id = min(component_ids, key=lambda k: R_map[k])
    weak_name, _ = comps[weak_id]

    # ---- output markdown ----
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append(f"# {EXPERIMENT_NAME}")
    lines.append(f"{args.student_id}，{args.student_name}")
    lines.append("")

    lines.append("## 1. 任务与剖面参数")
    lines.append(f"- 单循环时长（由 mission_profile 计算）：t_cyc = {t_cyc:.3f} h")
    lines.append(f"- 循环次数：N = {args.N}")
    lines.append(f"- 班次任务时间：T = N * t_cyc = {T:.3f} h")
    lines.append("")

    lines.append("## 2. 任务剖面（阶段时长）")
    lines.append("| 阶段 | duration_h |")
    lines.append("|---|---:|")
    for r in profile_rows:
        lines.append(f"| {r['phase']} | {r['duration_h']:.3f} |")
    lines.append("")

    lines.append("## 3. 你的 RBD（model.json）摘要")
    lines.append("```json")
    # 只展示 model 段，避免把 hints 一起打印
    lines.append(json.dumps(model, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")

    lines.append("## 4. 单元件参数与可靠度（R_i = exp(-λ_eff * T)）")
    lines.append("| 编号 | 元件 | λ(1/h) | duty | λ_eff(1/h) | R(T) |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for cid in component_ids:
        name, lam = comps[cid]
        lines.append(f"| {cid} | {name} | {lam:.2e} | {duty[cid]:.3f} | {lam_eff[cid]:.2e} | {R_map[cid]:.6f} |")
    lines.append("")

    lines.append("## 5. 系统任务可靠度")
    lines.append(f"- R_sys(T) = {R_sys:.6f}")
    lines.append("")

    lines.append("## 6. 薄弱环节（最小 R(T)）")
    lines.append(f"- {weak_id} {weak_name}：R(T) = {R_map[weak_id]:.6f}（λ_eff={lam_eff[weak_id]:.2e} 1/h）")
    lines.append("")

    lines.append("## 7. Sanity checks（必须通过）")
    lines.append(f"- 去冗余应变差：PASS（R_noRed={R_sys_stripped:.6f} ≤ R={R_sys:.6f}）")
    lines.append(f"- 缩短任务时间应变好：PASS（R_halfT={R_sys_half:.6f} ≥ R={R_sys:.6f}）")
    lines.append("")

    lines.append(f"> 报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # 保留自定义区块内容（如果已存在）
    custom_block_title = "## 8. 学生自定义补充区（请在此区块内补充任务1/3内容，不会被自动覆盖）"
    custom_block = f"{custom_block_title}\n\n### 任务1：建模与公式\n（请在此处补充你的建模思路、公式推导等）\n\n### 任务3：工程解释与改进建议\n（请在此处补充你的工程分析、薄弱环节解释、改进建议等）\n"
    if OUT_PATH.exists():
        old = OUT_PATH.read_text(encoding="utf-8")
        if custom_block_title in old:
            # 保留旧自定义区块内容
            custom_block = old.split(custom_block_title,1)[1].lstrip('\n')
            custom_block = f"{custom_block_title}\n" + custom_block

    lines.append(custom_block)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"已生成：{OUT_PATH}")
    print(f"R_sys(T={T:.3f}h) = {R_sys:.6f}")

if __name__ == "__main__":
    main()
