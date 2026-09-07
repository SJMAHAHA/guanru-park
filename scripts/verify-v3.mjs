import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {
  Box3,
  Group,
  Mesh,
  Texture,
  Vector3,
  Plane,
  PerspectiveCamera,
} from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import {
  MeshoptDecoder as Decoder,
  MeshoptEncoder as Encoder,
} from 'meshoptimizer';
import {
  applyGroups,
  LEVELS,
  PRESETS,
  ROOMS,
  groupState,
} from '../app/model-state.ts';
const manifest = JSON.parse(
  await fs.readFile('public/assets-v3/manifest.json', 'utf8'),
);
await Encoder.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({
    'meshopt.decoder': Decoder,
    'meshopt.encoder': Encoder,
  });
const docs = await Promise.all(
  manifest.assets.map((a) => io.read('public' + a.url)),
);
const files = await Promise.all(
  manifest.assets.map((a) =>
    fs.readFile('public/assets-v3/' + a.floor + '.bin'),
  ),
);
const bytes = Buffer.concat(files);
for (const a of manifest.assets) assert(a.bytes < 25 * 1024 * 1024);
// Actual Meshopt geometry decoding and glTF material/UV-transform loading.
// Texture creation is replaced with CPU Texture objects in this non-browser test;
// all embedded image bytes are separately decoded and checked with Pillow.
const loader = new GLTFLoader()
  .setMeshoptDecoder(MeshoptDecoder)
  .register(() => ({
    name: 'cpu_texture_validation',
    loadTexture: async () => {
      const texture = new Texture();
      texture.flipY = false;
      return texture;
    },
  }));
const root = new Group();
for (const doc of docs) {
  const binary = await io.writeBinary(doc);
  const part = await loader.parseAsync(
    binary.buffer.slice(
      binary.byteOffset,
      binary.byteOffset + binary.byteLength,
    ),
    '',
  );
  root.add(part.scene);
}
const gltf = { scene: root, scenes: [root] };
assert.equal(gltf.scenes.length, 1);
const groups = [];
let drawCalls = 0,
  triangles = 0,
  mappedMeshes = 0;
gltf.scene.traverse((n) => {
  if (n.userData.floor) groups.push(n);
  if (n instanceof Mesh) {
    drawCalls++;
    triangles +=
      (n.geometry.index?.count ?? n.geometry.attributes.position.count) / 3;
    const ms = Array.isArray(n.material) ? n.material : [n.material];
    if (ms.some((m) => m.map)) {
      mappedMeshes++;
      assert(n.geometry.attributes.uv, 'Textured mesh missing UVs');
    }
    const a = n.geometry.attributes.position;
    for (let i = 0; i < a.count; i++) {
      assert(Number.isFinite(a.getX(i)));
      assert(Number.isFinite(a.getY(i)));
      assert(Number.isFinite(a.getZ(i)));
    }
  }
});
assert.equal(groups.length, 29);
assert(drawCalls < 400);
assert(triangles > 1500000);
assert(mappedMeshes > 40);

assert(groups.every((g) => g.userData.version === '3.0'));
const initialBounds = new Box3().setFromObject(gltf.scene),
  size = initialBounds.getSize(new Vector3());
assert(
  size.x < 75 && size.z < 75,
  'Export must exclude the 1600-m Blender backdrop',
);
assert(size.y > 12 && size.y < 20);
const base = {
  floor: 'all',
  view: 'aerial',
  furniture: true,
  rotate: false,
  reset: 0,
  explode: false,
  reveal: false,
  cut: false,
  cutHeight: 13.2,
  evening: false,
  labels: true,
  focus: null,
};
for (const floor of ['B1', '1F', '2F', '3F']) {
  applyGroups(gltf.scene, { ...base, floor });
  const visible = groups.filter((g) => g.visible);
  assert(visible.length);
  assert(
    visible.every(
      (g) => g.userData.floor === floor && g.userData.category !== 'Ceilings',
    ),
  );
  assert(visible.some((g) => g.userData.category === 'Furniture'));
  const structure = visible.find((g) => g.userData.category === 'Structure');
  assert(structure);
  const bounds = new Box3().setFromObject(structure).getSize(new Vector3());
  assert(bounds.x > 15 && bounds.x < 55);
  assert(bounds.z > 15 && bounds.z < 60);
  applyGroups(gltf.scene, { ...base, floor, furniture: false });
  assert(
    groups
      .filter((g) => g.visible)
      .every((g) => g.userData.category !== 'Furniture'),
  );
}
applyGroups(gltf.scene, { ...base, reveal: true });
assert(
  groups
    .filter((g) => g.visible)
    .every(
      (g) =>
        !['3F', 'Roof'].includes(g.userData.floor) &&
        g.userData.category !== 'Ceilings',
    ),
);
applyGroups(gltf.scene, base);
const originalCenters = new Map(
  groups.map((g) => [g, new Box3().setFromObject(g).getCenter(new Vector3())]),
);
for (let repeat = 0; repeat < 3; repeat++) {
  applyGroups(gltf.scene, { ...base, explode: true });
  for (const g of groups) {
    const c = new Box3().setFromObject(g).getCenter(new Vector3()),
      o = originalCenters.get(g),
      offset = groupState(g.userData.floor, g.userData.category, {
        ...base,
        explode: true,
      }).offset;
    assert(Math.abs(c.y - o.y - offset) < 0.0001);
    assert(Math.abs(c.x - o.x) < 0.0001);
    assert(Math.abs(c.z - o.z) < 0.0001);
  }
  applyGroups(gltf.scene, base);
  for (const g of groups) {
    const c = new Box3().setFromObject(g).getCenter(new Vector3());
    assert(c.distanceTo(originalCenters.get(g)) < 0.0001);
  }
}
const plane = new Plane(new Vector3(0, -1, 0), 4.7);
assert(plane.distanceToPoint(new Vector3(0, 5, 0)) < 0);
assert(plane.distanceToPoint(new Vector3(0, 4, 0)) > 0);
for (const [name, p] of Object.entries(PRESETS)) {
  const camera = new PerspectiveCamera(p.fov ?? 38, 1, 0.045, 600);
  camera.position.fromArray(p.position);
  camera.lookAt(new Vector3(...p.target));
  camera.updateMatrixWorld(true);
  const projected = new Vector3(...p.target).project(camera);
  assert(
    Math.abs(projected.x) < 1e-5 && Math.abs(projected.y) < 1e-5,
    `${name}: camera misses target`,
  );
}
for (const room of ROOMS) {
  assert(room.position.every(Number.isFinite));
  assert(room.position[1] === LEVELS[room.floor]);
}
let textureCount = 0,
  bakedMeshes = 0;
for (const doc of docs) {
  textureCount += doc.getRoot().listTextures().length;
  for (const mesh of doc.getRoot().listMeshes())
    for (const p of mesh.listPrimitives()) {
      if (
        p.getMaterial()?.getName().startsWith('V3 ') &&
        p.getMaterial().getName().includes(' floor ')
      ) {
        assert(p.getAttribute('TEXCOORD_1'), 'Missing baked UV2');
        bakedMeshes++;
      }
    }
}
assert(bakedMeshes >= 7);
const report = {
  version: '3.0',
  sha256: crypto.createHash('sha256').update(bytes).digest('hex'),
  scenes: 1,
  groups: groups.length,
  drawCalls,
  triangles,
  mappedMeshes,
  textures: textureCount,
  bakedMeshes,
  megabytes: +(bytes.length / 1e6).toFixed(2),
  bounds: size.toArray(),
  singleFloorAndFurnitureChecks: true,
  roofRevealCheck: true,
  explosionRoundTripChecks: 3,
  cameraTargetsChecked: Object.keys(PRESETS).length,
  roomAnchorsChecked: ROOMS.length,
};
await fs.writeFile(
  'work/model-validation-v3.json',
  JSON.stringify(report, null, 2),
);
console.log(JSON.stringify(report, null, 2));
