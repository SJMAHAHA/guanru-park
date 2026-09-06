import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { Box3, Mesh, Vector3 } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
const bytes = await fs.readFile('public/villa.glb');
const gltf = await new GLTFLoader()
  .setMeshoptDecoder(MeshoptDecoder)
  .parseAsync(
    bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
    '',
  );
assert.equal(gltf.scenes.length, 1);
const groups = [];
let drawCalls = 0,
  triangles = 0;
gltf.scene.traverse((n) => {
  if (n.userData.floor) groups.push(n);
  if (n instanceof Mesh) {
    drawCalls++;
    triangles +=
      (n.geometry.index?.count ?? n.geometry.attributes.position.count) / 3;
  }
});
assert.equal(groups.length, 23);
assert(drawCalls < 150, `Too many draw calls: ${drawCalls}`);
for (const f of ['B1', '1F', '2F', '3F', 'Roof', 'Site'])
  assert(groups.some((n) => n.userData.floor === f));
for (const floor of ['B1', '1F', '2F']) {
  const structure = groups.find(
    (n) => n.userData.floor === floor && n.userData.category === 'Structure',
  );
  assert(structure);
  const dimensions = new Box3().setFromObject(structure).getSize(new Vector3());
  assert(dimensions.x > 25 && dimensions.x < 55);
  assert(dimensions.z > 25 && dimensions.z < 60);
  assert(
    groups.some(
      (n) => n.userData.floor === floor && n.userData.category === 'Furniture',
    ),
  );
  assert(
    groups.some(
      (n) => n.userData.floor === floor && n.userData.category === 'Ceilings',
    ),
  );
}
assert(bytes.length < 25 * 1024 * 1024);
console.log(
  JSON.stringify(
    {
      scenes: gltf.scenes.length,
      groups: groups.length,
      drawCalls,
      triangles,
      megabytes: +(bytes.length / 1e6).toFixed(2),
    },
    null,
    2,
  ),
);
