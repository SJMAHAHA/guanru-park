# Guanru Park 2.0 · 建筑漫游

Blender 精细建筑模型的交互展示。支持整栋、B1 / 1F / 2F / 3F 独立楼层，分层展开、揭开屋顶、水平剖切、日景和傍晚、家具显隐、房间标签与聚焦，以及 8 个整体或室内外视角。效果图集提供 12 张 Blender 正式渲染。手机支持单指旋转和双指缩放、平移。

模型以米为单位，层高约 3.15 m；尺寸依据参考截图推定。2.0 保留原体量与平面洞口，新增建筑收口、家具软装与厨卫细节。网页使用 UV PBR 纹理与实时光照，和 Blender 离线渲染并非逐像素一致。

## 开发

```sh
npm install
npm run dev
npm run build
```

## 模型处理与验证

`public/villa-v2.glb` 包含 24 个楼层用途组、约 195 万三角面及 19 张嵌入纹理，约 19.28 MB。按材质合并为 167 次绘制，并量化、Meshopt 压缩；未减面。纹理 UV 量化前归一化，并使用 KHR_texture_transform 保持实体纹理尺度。

```sh
node scripts/optimize-model.mjs /absolute/path/to/web_export/villa.glb
node --experimental-strip-types scripts/verify-model.mjs
npx tsc --noEmit
npm run lint -- app/page.tsx app/viewer.tsx app/model-state.ts app/layout.tsx scripts/optimize-model.mjs scripts/verify-model.mjs
npm run build
```

验证脚本用实际 Three.js GLTFLoader 与 Meshopt 解码，检查几何、UV、文件尺寸、楼层隔离、家具显隐、展开复位、屋顶揭开、剖切方向、相机目标与房间标记。图像加载以 CPU 桩替代，另用 Pillow 解码导出的嵌入图片；未执行浏览器 GPU 视觉与点击测试。

`app/model-state.ts` 定义空间选项、相机、房间及分组显隐；`app/viewer.tsx` 负责 Three.js 渲染与相机；`app/page.tsx` 和样式负责控制面板及画廊。
