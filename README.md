# 实验 1：完整搬运循环任务可靠度评估（RBD + 任务剖面）

本仓库是**学生版**最简可复现模板：你需要补全 **任务剖面（mission profile）** 与 **RBD 结构（model.json）**，
程序才能计算并生成 `output/experiment_result.md`。

实验的完整描述见 `description.md`。

---

## 1. 你需要完成的两件事（必做）
### A) 任务剖面：`data/mission_profile.csv`
- 填写 5 个阶段（Pick / Lift / TravelLoaded / Place / ReturnEmpty）的 **持续时间**（小时），已经给出两行示例
- 对每个阶段，标注各元件是否“处于工作/受载/关键参与状态”（必须为0/1）
- 自定义 N、任务剖面阶段时长
- 程序会自动计算每个元件的占空比：`duty = (该元件工作总时长) / (总任务时长)`

> 注意：并非所有元件都只在某些阶段工作；例如，供电/PLC/安全链通常全程工作，标记为 1。

### B) RBD 结构：`data/model.json`
- 用 JSON 表达你的可靠性框图（串联/并联/组合）
- 你必须把系统成功事件对应的**完整链路**建模出来
- 模板中包含占位符（__FILL__），不允许直接运行
- 最简示例：  
```
  "model": {
      "series": [
        "C1",
        "C2"]
},
```
- 完整的链路需要根据你定义的任务剖面来建模，例如：  
  - 如果某个元件在所有阶段都工作，那么它应该在 RBD 中的每个阶段都出现（例如供电链）
  - 如果某个元件只在特定阶段工作，那么它只需要在对应阶段的 RBD 中出现（例如编码器冗余只在起升链）
- 任务剖面通常包括五个动作（pick、lift、travelloaded、place、returnempty），每个动作有自己的持续时间（duration），并在每个阶段标明哪些元件参与（用1表示参与，0表示未参与）。
这样可以准确计算每个元件的工作时间占比（duty），用于后续的可靠性分析。
---

## 2. 一键运行
在仓库根目录执行（示例,姓名使用拼音或英文）：

```bash
python src/calc.py --student_id 2026XXXXXX --student_name zhangsan --N 60
```

- `--N`：循环次数（默认 60，需自行调整）
- 单循环时长 `t_cyc` 来自 `data/mission_profile.csv` 的五阶段时长之和
- 运行后生成：`output/lab1_report_<student_id>_<student_name>.md`

---

## 3. 输入数据
- `data/components.csv`：元件失效率（λ，单位 1/h）
- `data/mission_profile.csv`：阶段时长 + 元件工作标记（0/1），需要补全
- `data/model.json`：RBD 结构（需要补全）

---

## 4. 输出报告格式（已内置）
- 第1行：实验名称（Markdown 一级标题）
- 第2行：学号、姓名
- 第3行起：实验结果（参数、RBD摘要、表格、子系统、子系统可靠度、系统可靠度、薄弱环节、sanity checks）
- (可选) 子系统可靠度部分未在 calc.py 中内置，需要你编程实现（提示：可以在 `calc.py` 中定义一个函数 `calculate_subsystem_reliability()` 来计算并返回各子系统的可靠度）

---

## 5. 内置 sanity checks（必须通过）
程序会自动做两项基本自检：
1) **去冗余应变差**：把所有并联节点替换为单支路后，系统可靠度应不高于原结果  
2) **缩短任务时间应变好**：把总任务时间减半后，系统可靠度应更高

若不满足，说明你的 **任务剖面** 或 **RBD** 很可能有问题，请先修正再提交。

---

## 6. AI 使用规则（课程要求可写入报告末尾）
- 允许：解释公式、查错、优化排版、辅助写代码（必须核验）
- 禁止：不经核验直接生成整份报告/整套模型并提交
- 必须：给出你如何核验并修正至少 1 个 AI 输出错误点（单位/并联公式/占空比/边界等）

## 7. 提交物 (submissions)

1. `experiment_result_<student_id>_<name>.md`（必须，要求见 `description.md` 的要求五）
2. `calc.py`（或同等 Python 脚本，必须可运行）
3. `data/components.csv`(如有修改，必须提交)
4. `data/mission_profile.csv`(必须提交)
5. `data/model.json`：RBD 结构如不同于description.md中的示例，也必须提交

---

## 0. 重要说明与常见问题

### 参数与数据自定义
- 默认所有同学的数据文件（components.csv、mission_profile.csv、model.json）一致，结果也一致。
- 如需个性化实验结果，可自行调整 N、任务剖面、RBD结构或元件参数。
- 在自定义区块说明你的个性化修改内容。

### 结果文件命名与归档
- 程序自动生成结果文件，命名为：`experiment_result_{student_id}_{student_name}.md`，请勿手动更改。
- 所有结果自动归档到 output/ 目录，便于批量收集和自动化检查。

### 手动补充区块说明
- 自动生成区块（参数、表格、RBD等）请勿手动修改，否则自动化检查时会被覆盖。
- 请在“## 8. 学生自定义补充区”内补充建模思路、公式推导、工程解释等内容。

### 批量自动运行与归档（教师/助教参考）
- 可用脚本批量运行所有学生的 calc.py，并自动归档结果。
- 示例：
  ```bash
  for d in submissions/*; do
    id=$(basename "$d" | cut -d_ -f1)
    name=$(basename "$d" | cut -d_ -f2)
    python src/calc.py --student_id "$id" --student_name "$name" --N 60
  done
  ```

### 结果一致性与个性化
- 不修改数据时，所有同学结果一致。
- 如需差异，请按要求个性化数据或参数，并在自定义区说明。

### 提交物清单
- `experiment_result_{student_id}_{student_name}.md`（自动生成，含自定义补充区）
- `calc.py`（如有修改需一并提交）
- 数据文件（如有个性化修改需一并提交）

### 常见错误与解决方法
- 参数未填写或格式错误：请检查命令行参数和数据文件格式。
- 结果文件被覆盖：请只在自定义补充区填写手动内容。
- 自动化检查未通过：请检查 sanity check、RBD结构和任务剖面。

---

## 附录：Git 基础使用方法资源

- [Git 官方文档（简体中文）](https://git-scm.com/book/zh/v2)
- [Git 官方英文文档](https://git-scm.com/doc)
- [Git Cheat Sheet（官方速查表）](https://education.github.com/git-cheat-sheet-education.pdf)
- [廖雪峰的 Git 教程](https://www.liaoxuefeng.com/wiki/896043488029600)
- [菜鸟教程 Git](https://www.runoob.com/git/git-tutorial.html)
- [VS Code 官方 Git 指南](https://code.visualstudio.com/docs/sourcecontrol/overview)

以上资源适合初学者快速学习 Git 的基本操作和常用命令。