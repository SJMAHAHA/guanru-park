# 重建与文件对应关系

1. Blender 使用 `--factory-startup -b --python build_villa.py` 生成 `Guanru_Park_3.0.blend`。脚本调用 `details_v2.py` 及 3.0 增量 `details_v3.py`，保留建筑参考坐标。
2. 打开生成文件，执行 `polish_and_bake.py`：补齐安装支撑、主卫修正、餐厅吊灯、相机，并以 Cycles 烘焙 B1/1F/2F/3F 地面间接光。所有主要材质图片已经打包进最终 .blend。
3. 用最终文件执行 `export_mirrors.py`，再执行 `web_export/export_web.py`。省略参数导出全楼；`-- 1F` 可只更新 1F。输出按楼层保存，临时导出场景不覆盖原生模型。
4. 在网页工程运行 `node scripts/optimize-v3.mjs '../guanru park/展示模型_3.0/web_export'`。生成 Meshopt 几何、外置共享纹理及资源清单；按 `public/assets-v3/textures/high` 生成最长边 1024 的 `standard` 同名变体。
5. 使用 `render_views.py -- all` 输出离线图；`prepare_delivery.py` 将本版渲染图转换到网页图集，并生成浏览器对比入口。

`room_schedule.json` 是逐间交付清单；`qa/room-audit.json` 为按几何范围统计的安装对象记录，非碰撞求解或施工验收。`qa/validation.json` 检查有限值、纹理依赖和主要家具与墙面包围盒交叉；正常支撑接触不视为穿模。

Blender 坐标到网页坐标：`[x, y, z] → [x, z, -y]`。层高 3.15 m，建筑参考比例为 18.75 px/m。
