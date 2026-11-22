# Q1 LaTeX 草稿

- 主文件：`Q1.tex`
- 类文件：`mcmthesis.cls`（来自用户提供的 MCM/ICM 模板）
- 当前输出：`Q1.pdf`，A4，共 13 页（Summary Sheet + 目录 + 11 页正文）
- 字体：`ctex` 的 `fontset=fandol`；若本机缺少 Fandol，可改为 `fontset=windows`

## 编译

在 `正稿/Q1-v0/latex/` 下运行：

```powershell
xelatex Q1.tex
xelatex Q1.tex
```

或：

```powershell
latexmk -xelatex Q1.tex
```

需要运行两遍以生成目录、页码和引用。

## 当前状态

- 正文结构：问题与判据 → 三条总假设 → 电力 → 水 → 土地 → 集成 → 案例结果 → 局限与结论。
- 图表：图 1–8、表 1–4 均为占位框/占位表，待填入正式图形与数值。
- 结果：`【待填】` 处需要案例场址与 `P_E/P_W/P_L` 计算结果。
- 参考文献：使用 `thebibliography` 的临时编号，定稿时可换成模板的 `biblatex` 或按出现顺序重排。
- Summary Sheet 的 “Problem Chosen / Team Control Number” 仍沿用 MCM 模板英文标签；若要全中文，可改 `mcmthesis.cls` 或自绘 summary sheet。
