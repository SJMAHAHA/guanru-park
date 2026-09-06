# Guanru Park · 建筑漫游

Blender 建筑模型的实时网页展示。支持完整建筑、B1 / 1F / 2F 独立楼层、鸟瞰 / 东侧 / 中庭 / 正交俯视、家具显示、自动旋转、缩放与视角重置。手机支持单指旋转和双指缩放、平移。

模型以米为单位；层高约 3.15 m。尺寸依据参考截图推定。网页使用适配后的实时材质，保留主要颜色、玻璃透明度、灯光和阴影，未烘焙 Blender 程序化纹理；正式效果图作为加载预览及错误回退。

## 开发

```sh
npm install
npm run dev
npm run build
```

## 模型处理与验证

网页模型包含 23 个楼层/用途组，保留原始体量和家具几何，并按材质合并绘制、量化与 Meshopt 压缩。`scripts/optimize-model.mjs` 接收 Blender 导出的 GLB 路径，写入 `public/villa.glb`。

```sh
node scripts/optimize-model.mjs /path/to/export/villa.glb
node scripts/verify-model.mjs
npx tsc --noEmit
npm run lint -- app/page.tsx app/viewer.tsx app/layout.tsx scripts/optimize-model.mjs scripts/verify-model.mjs
```

验证脚本实际通过 Three.js 和 Meshopt 解码模型，检查场景数量、分层标记、家具与顶棚组、空间尺度、绘制数量和文件大小。没有自动执行浏览器视觉或交互测试。

站点首次发布设为仅所有者访问。原 Blender 工程继续作为可编辑建模源。
