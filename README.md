# 水的固—液—气三维 p–v–T 状态图谱

基于 **NISTIR 5078 表 1、2、3** 和 **Feistel & Wagner (2006) 表 11、18、19、20** 的可追溯数值表重建。没有使用 CoolProp、IAPWS、REFPROP，也没有实现状态方程或理想气体补点。

## 直接使用

用桌面版 **Chrome 或 Edge 双击 `dist/index.html`** 即可打开。全部数据、Plotly.js 和界面脚本内嵌在约 15 MB 的 HTML 中，无需联网或 Python。点击“导出 PNG”会打开“另存为”，可选择目录和文件名；建议文件名包含视图和本地导出时间，例如 `water-pvt-tv-20261023-143025.png`。

首次使用可先在左侧选择相区，再用顶部按钮切换三维或二维视图。点击曲面查看状态及表格来源；“曲面不透明度”仅调整显示效果，数值越高颜色越实。

浏览器标签图标只在构建时设置，网页没有供访问者修改的入口。把自己设计的图片命名为 `favicon.png`、`favicon.jpg` 或 `favicon.jpeg`，放到 `web/` 目录，再运行 `python scripts/build_html.py`。构建时会将图片缩为 128×128 像素并内嵌进 `dist/index.html`，原图不变。若同时存在多个文件，优先顺序为 PNG、JPG、JPEG；没有这些图片时使用默认的 `web/favicon.svg`。JPG 不支持透明背景，需要透明效果时选 PNG 或 SVG。发布时只需发布生成的 HTML。如果重新构建后标签仍显示旧图标，请关闭旧标签，再重新打开 `dist/index.html`；也要确认打开的不是旧版 HTML 副本。

`Start-Water-PVT.cmd` 或 `python launch.py` 是可选的本机网页启动方式，需要 Python 3。它们不负责保存 PNG，也不会创建 `exports`。旧版本生成的 4 张测试图片已移到 `tests/legacy_exports/` 保留；此目录不进入交付包。若其他副本仍有 `exports`，其中只是旧版导出的图片。

## 已实现

- 冰 Ih、液态水、水蒸气三个单相网格，以及固液、汽液、固气三个共存网格。超临界流体另有独立图层，默认关闭。
- 鼠标旋转、以光标位置为中心滚轮缩放、平移；单独开关各相区、原表点、相平衡边界、三相线和临界点；调节透明度及重置视角。
- p、v 分别切换线性或对数；悬停始终显示真实 SI 数值、相态、来源 ID、数据类型和适用的质量分数。
- 三维、p–T、p–v、T–v 四种视图。二维直接投影同一网格顶点和边界，单相以点云表达，未另行拟合状态函数。
- 工程教学总览、全部数据域、冰水体积细节、临界区四个范围预设。
- 点击点/曲面查看父表行详情。面内悬停显示最近顶点信息，不能视为任意状态的精确查询。
- 选择表 2 的原始饱和压力，调节汽液干度 x，播放汽化过程；端点直接来自表 2。该压力若同时在表 3 中，则显示同压力的加热/过热原表路径。
- PNG 导出、完整模型 JSON 导出、中文来源和方法说明面板。

## 数据规模和来源

| 表格 | 结构化记录 | 用途 |
|---|---:|---|
| NIST 表 1：饱和温度表 | 375 | 汽液边界及两相面，临界终点 |
| NIST 表 2：饱和压力表 | 272 | 精确选取表内定压相变行，交叉校验 |
| NIST 表 3：压缩水和过热蒸气 | 9524 | 流体单相顶点；包含保留但不显示的亚稳/外推条目 |
| Feistel–Wagner 表 11：密度 | 164 | 冰 Ih 顶点；稳定性筛选前的原表记录 |
| 表 18：关键状态 | 2 | 三相点、常压熔点核对 |
| 表 19：熔化平衡 | 26 | 固液端点；只显示其中保守低压部分 |
| 表 20：升华平衡 | 30 | 固气端点 |

公开入口：[NISTIR 5078](https://www.nist.gov/system/files/documents/srd/NISTIR5078.htm)、[Feistel & Wagner PDF](https://www.teos-10.org/pubs/Feistel_and_Wagner_2006.pdf)。完整来源、页码、单位、提取陷阱及权利条件见 **DATA_SOURCES.md**。原文件 SHA-256 在 `raw_data/manifest.json`。

公开表本身是文献作者由物性模型制成的表格，本项目只提取这些已发表数值，不把所有条目说成实验测量点。每个模型顶点可追溯到表行，插值样本有单独标记。

## 从头构建

建议 Python 3.11–3.13（本机验证为 3.13）。首次安装：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python build.py --download
```

已有原始文件时执行 `python build.py`，会依次提取、重建、校验、生成 HTML。下载脚本对已存在文件不覆盖。

本机代理曾使 TLS 失败，已通过 Windows curl 的直接连接完成下载。如遇同样问题，可执行：

```powershell
python build.py --download --curl --direct
```

`--direct` 绕过代理；`--curl` 使用 Windows curl 的 `--ssl-no-revoke` 以避开离线吊销查询，仍验证 HTTPS 证书。默认 Python 下载路径不修改 TLS 验证。其他操作系统通常不需要这两个选项。

独立步骤：

```powershell
python scripts/download_data.py
python scripts/extract_tables.py
python scripts/build_model.py
python tests/validate_data.py
python scripts/build_html.py
```

几何构建可能需要约一分钟。最终使用不需要这些构建依赖。

## 目录

```text
raw_data/           原始 PDF、NIST 使用说明、下载 URL 与 SHA-256
processed_data/     CSV、model.json、排除原因、模型统计、验证报告
scripts/           下载、PDF 提取、模型与离线网页生成
src/geometry.py    几何剖分、边界筛选、两相混合；无物性方程
web/               中文界面模板和交互脚本
dist/index.html    可直接打开的离线网页
tests/             数值校验、浏览器验收、截图及导出 PNG
build.py           顺序构建入口
Start-Water-PVT.cmd Windows 双击启动入口
launch.py          可选的本机网页启动器（Python 标准库）
DATA_SOURCES.md    数据字典、来源、精度与权利条件
```

`raw_data/` 中的页面 PNG、版面文本是本地人工复核资料，不参与数值生成。GitHub 提交和分发压缩包只保留 `raw_data/manifest.json`；原始 PDF、网页存档与截图保留在本机，重新获取请运行 `python build.py --download`。测试截图、报告和本机缓存也不进入 GitHub 提交。

## 发布到 GitHub

先在 GitHub 网站创建空仓库，不要勾选自动生成 README、`.gitignore` 或许可证。然后在本项目目录运行：

```powershell
git init -b main
git add .
git status --short
git commit -m "Initial release of water p-v-T atlas"
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

执行 `git status --short` 时确认没有原始论文 PDF、`.venv/`、测试截图和本机导出文件。`git push` 可能要求通过浏览器登录 GitHub。上传仓库只发布源代码与构建好的 HTML；若还希望别人通过网页地址直接使用相图，需要另外配置 GitHub Pages。公开前也应确认自定义 `web/favicon.png` 的使用权，因为它会进入仓库并内嵌在 HTML 中。

## 物理意义与几何方法

单相 p–v–T 状态满足两个独立自由度，表内 (T,p) 对应 v，形成二维曲面。先按原表斜体与相平衡数据排除亚稳态，再在 (T/100, log₁₀p) 平面做 Delaunay 三角剖分。设置最大边距，按重心采样检查相区，剔除跨越相界的面；仅平衡曲线上的点不能凭空构造单相曲面。内部 v 为分片线性几何近似，没有生成新的精确物性值。

两相共存时 p、T 沿平衡线对应，每行的两个比体积端点连接成线段。使用 v=(1−x)v₁+xv₂，沿公开相邻平衡行做有限范围几何插值，构成共存面。x 依次表示固液面的液体质量分数、汽液面的蒸气质量分数（干度）、固气面的蒸气质量分数。对数展示只改变坐标，不改变质量守恒。

三相点的 T=273.16 K、p=611.657 Pa 固定，但三相质量比例变化会改变总体 v，所以在三维中是沿 v 的线段；投影到 p–T 才是一个点。单一 v 不能唯一反推出三种质量比例，因此三相线不提供唯一“干度”。

临界点取 T=647.096 K、p=22.064 MPa、v=0.0031056 m³/kg（原表舍入值）；汽液端点在这里合并，共存面终止，干度不再定义。

冰在熔化后体积减小，因此表 19 的 Δv熔化 为负，固液平衡 dp/dT<0。该关系来自公开数值表，不是通过本项目求解 Clapeyron 方程获得。

## 实际边界与不足

1. **冰 Ih 是保守子域**：单相冰只显示 130–273.16 K、p≤50 MPa；流体 p≤100 MPa；固液面只至表内 92.3352 MPa。其他冰型不显示，空白不代表不存在稳定状态。
2. **缺口真实保留**：冰表只有少量压力列，低温单相蒸气没有足够的离开升华线的数据，部分接缝和低压冰面留白。不能只靠弯曲的平衡线捏出单相蒸气面。
3. **原表有限精度**：绝大多数 NIST 数值约五位有效数字。三相压力的舍入差仅在几何连接中标准化到表 18 / 表 2 值，CSV 保留原值。不同来源同相体积还有约 ppm 级接缝。
4. **插值没有物性误差保证**：剖分筛选和边距约束是保守几何规则，重心取样不等于连续全域数学证明；稀疏区域不用于高精度物性计算。对数压力插值尤其在稀疏冰区只能作教学观察。
5. **视图可能重叠**：二维投影不是单值函数；透明 WebGL 网格存在排序局限。可隐藏相区或使用专用细节视图。
6. **定压实验只选公开压力行**：不提供任意 p 的物性求解；没有该压力表 3 数据时，只显示饱和相变段。
7. **版权分开处理**：公开访问不等于开放再分发。冰论文保留在本地供复核，分发 ZIP 排除完整论文与截图，详见 DATA_SOURCES.md。项目代码的 MIT 许可不覆盖原文献。

可扩展方向：增加权利条件明确的公开低温蒸气与低压冰数值表、更多离开相界的冰密度列、约束剖分与误差可视化，以及带独立权威边界的其他冰晶型。

## 验证

数值检查：`python tests/validate_data.py`。包括文件哈希、完整行数、ρv 一致性、体积单位、科学计数法、熔化负斜率、临界合并、三相压力连接、网格索引与质量分数范围。结果写入 `processed_data/validation_report.json`。

浏览器检查需要 Node.js、Playwright 和 Chrome：

```powershell
npm install --no-save playwright
node tests/browser_smoke.cjs
```

Windows 默认 Chrome 路径已配置；可用环境变量 `CHROME_PATH` 覆盖。测试脚本需要本地安装的 Playwright。测试以 `file://` 打开 HTML，并拦截 HTTP 请求以验证离线运行；实际操作投影、坐标切换、干度、图层、旋转、重置、来源，并模拟系统“另存为”接口检查默认文件名与 PNG 内容。报告在 `tests/browser_report.json`，截图在 `tests/overview.png`、`tests/condensed.png`。实际系统文件选择窗口仍需人工检查。

交付前已在项目 `.venv` 中运行完整 `build.py`：从原始 PDF 重新提取、剖分、校验并生成网页，重建前后 `model.json` 的 SHA-256 完全一致，见 `tests/reproducibility_report.json`。自动浏览器测试通过，运行时 HTTP 请求数和页面错误数均为零。PNG / JSON 已实际导出到测试目录。

2026-10-23 的 `tests/local_export_report.json` 与 `tests/local_export_zone_report.json` 是旧版本固定目录导出的历史验证记录，里面的原始 `exports` 路径已失效；图片现存于 `tests/legacy_exports/`。当前网页改用浏览器“另存为”，上述记录不代表当前导出方式的验证结果。

可用 `python scripts/package_project.py` 生成交付压缩包 `water-pvt-project.zip`。压缩包包含源代码、CSV/JSON、离线网页和验证记录；原始论文/PDF 不打包，接收者需要从原始链接重新获取时执行 `python build.py --download`。
