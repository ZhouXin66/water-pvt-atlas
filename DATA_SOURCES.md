# 数据来源、字段和使用条件

下载核实日期：2026-10-21。每个原始文件的 URL、字节数、SHA-256 和获取时间见 `raw_data/manifest.json`。数字来自已发表的数值表；本项目没有计算物性状态方程。

## A. NISTIR 5078

Allan H. Harvey (1998), *Thermodynamic Properties of Water: Tabulation from the IAPWS Formulation 1995 for the Thermodynamic Properties of Ordinary Water Substance for General and Scientific Use*, NISTIR 5078.

- 目录：<https://www.nist.gov/system/files/documents/srd/NISTIR5078.htm>
- 表 1：<https://www.nist.gov/system/files/documents/srd/NISTIR5078-Tab1.pdf>，7 页、375 行（含临界行），保存为 `saturation_temperature.csv`。
- 表 2：<https://www.nist.gov/system/files/documents/srd/NISTIR5078-Tab2.pdf>，5 页、272 行（含临界行），保存为 `saturation_pressure.csv`。第一行 p 的单位明确为 Pa，其他行为 MPa。
- 表 3：<https://www.nist.gov/system/files/documents/srd/NISTIR5078-Tab3.pdf>，60 页、提取 9524 条有数值的压力/温度记录，保存为 `fluid_table3.csv`。每页有三个压力块，第一块复用第二块的温度列；每个亚临界等压线的首两行是饱和液、饱和气。
- 说明：<https://www.nist.gov/system/files/documents/srd/NISTIR5078-Text.pdf>。

单位：温度 °C 加 273.15 得 K；MPa 乘 10⁶ 得 Pa；v 的 cm³/g 乘 10⁻³ 得 m³/kg；ρ 为 kg/m³。直接使用原表 v，独立用 ρv≈1 检查单位和提取。两者均有舍入，不强制使其完全互为倒数。

说明正文指出，大多数值约五位有效数字；表 3 的斜体条目是相平衡固态区域内的亚稳液体；超过 1000 °C 的条目是原出版物的外推。项目保留这些原表记录但从稳定显示中排除。本项目额外限制流体 p≤100 MPa。全部排除记录见 `processed_data/excluded_rows.json`。

### NIST 使用条件

查阅并保存了官方说明：<https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications>。

该说明区分 SRD 数据库版权、其他 NIST 雇员作品及 NIST Technical Series。NISTIR 5078 是公开技术报告，其公开表格在本地研究中使用并完整标注来源。不能据此推断 NIST-10 软件或全部 SRD 数据库也可自由复制。本项目未使用 NIST-10 软件或受订阅限制的数据服务。

修改说明（2026-10-21）：从公开 PDF 提取指定物性字段、单位换算、稳定性筛选、几何剖分和两相混合；原始 CSV 保留公开数值的舍入精度。非 NIST 官方制品；NIST 不为本项目的重建、准确性或适用性背书。数据按原来源的 AS IS 条件使用。

## B. Feistel & Wagner (2006)

Rainer Feistel and Wolfgang Wagner, *A New Equation of State for H₂O Ice Ih*, J. Phys. Chem. Ref. Data **35**, 1021–1047 (2006). DOI: <https://doi.org/10.1063/1.2183324>。

公开 PDF：<https://www.teos-10.org/pubs/Feistel_and_Wagner_2006.pdf>。

| 表 | PDF 页 / 印刷页 | 本项目使用字段 | 提取记录 |
|---|---|---|---:|
| 11 | 20 / 1040 | T、p、ρ（kg/m³），v=1/ρ | 164 |
| 18 | 25 / 1045 | 三相点和常压熔点 p、T、v（m³/kg） | 2 |
| 19 | 25 / 1045 | T、p（MPa）、v冰、Δv熔化（cm³/kg） | 26 |
| 20 | 26 / 1046 | T、p（Pa）、v冰、Δv升华（cm³/kg） | 30 |

v冰 是冰的比体积，不是液体或蒸气的比体积。表 19 中 Δv=v液−v冰，为负；表 20 中 Δv=v气−v冰，为正。两者体积字段均乘 10⁻⁶ 换成 m³/kg，然后相加得到另一相比体积。130 K 行 p=1.2004×10⁻⁸ Pa，Δv=4.9982×10¹⁸ cm³/kg。

特殊字体修复：PDF 的 `MathematicalPi-One` 字体把正号、负号编码成普通的字符 `1`、`2`；只对该字体替换成 +、−，普通数字不变。按列坐标读取，保留正负号和科学计数法。表格横杠视为缺值，不补零。保留原始 v 和 Δv 字段以便检查。

### 冰 Ih 的边界和使用条件

论文明确指出其图表没有考虑相邻冰 II、III、IX、XI 等的精确相界。不能将表 11 的整个数值范围当作稳定 Ih。项目单相冰只展示 T≥130 K、p≤50 MPa 的保守区域，并检查熔化和升华边界；固液混合面只使用至 92.3352 MPa 的表行（下一行超过项目的 100 MPa 上限），不使用其 217 MPa 行延续 Ih。

PDF 标注 © 2006 American Institute of Physics，未找到该 PDF 的明确 CC 或同类开放再分发许可。公开可下载不等于开放版权。本项目保留完整 PDF 供本地研究和提取复核；可分发压缩包不包含该论文、PDF 页面图像或全文提取文本。网页和 CSV 仅引用相关数值事实，重新组织为教学模型并注明作者、表号和页码，不复刻原文排版、图像或论文正文。对完整论文再发布不授予许可，后续商业或大范围数据分发应自行确认权利条件。本文件不是法律许可。

## 每条数据的追溯

CSV 行有唯一 ID、来源、表号、PDF 页码、原始字段及 SI 单位字段。`model.json` 的 `references` 可按 ID 追溯；每个网格顶点含 `[T_K,p_Pa,v_m3_kg,来源ID,数据类型,x]`，插值点记录相邻父行 ID。三角面通过顶点索引关联这些信息。`published table` / `published endpoint` 也可能有单位换算或边界压力标准化，均有明确记录，绝非“未经处理的测量值”。这些公开数值表本身也是文献作者的计算结果，而非所有点都是实验测量。

三相连接标准化只作用于几何模型：表 19 的 0.0006 MPa、表 20 的 611.66 Pa、NIST 表 1 的 0.0006117 MPa 统一到表 18 / NIST 表 2 的 611.657 Pa。常压熔点 0.1013 MPa 统一到表 18 的 101325 Pa。模型另存 `printed_p_Pa`，CSV 不改原值。三相液体和蒸气端点之间、不同来源同相体积的微小舍入差保留，最大三相蒸气差约 5 ppm。

## 几何插值的处理记录

单相 Delaunay 参数为 (T/100,log₁₀p)。剔除 ΔT>101 K 的边；流体剔除 Δlog₁₀p>0.65 的边，冰为 3。每个三角形至少包含一个来自单相物性表的顶点，不能仅由平衡曲线生成单相片。每个三角形在 1/8 重心网格取样，对照同一份公开平衡表的分段插值筛除跨相面。该离散检查和保守留白减少跨界风险，不是对曲面插值误差的严格数学上界。

两相面：在每两行之间细分四段；T 和两端 v 线性插值，log₁₀p 线性插值。每条两相连线 25 个展示样本，v=(1−x)v₁+xv₂。汽液、固气按 v 的对数间距选择样本，以免坐标变换后失真；x 仍是从该关系反算的质量分数。临界行 v₁=v₂，x 标为未定义，并焊接成一个顶点、剔除退化面。几何插值不增加物性有效数字，不跨越相界、不外推到覆盖外。
