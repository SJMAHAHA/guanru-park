import { NodeIO } from '@gltf-transform/core';
import {
  ALL_EXTENSIONS,
  KHRTextureTransform,
} from '@gltf-transform/extensions';
import { dedup, weld, join, meshopt } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
await MeshoptEncoder.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({
    'meshopt.encoder': MeshoptEncoder,
    'meshopt.decoder': MeshoptDecoder,
  });
if (!process.argv[2]) throw Error('Provide the Blender GLB export path.');
const doc = await io.read(process.argv[2]);
await doc.transform(dedup(), join({ keepMeshes: true }), weld());
// Physical repeating UVs are normalized per material, retaining repeat and offset
// with KHR_texture_transform. This permits 16-bit UV storage without changing scale.
const extension = doc.createExtension(KHRTextureTransform);
for (const material of doc.getRoot().listMaterials()) {
  const infos = [];
  for (const key of [
    'BaseColor',
    'Normal',
    'MetallicRoughness',
    'Occlusion',
    'Emissive',
  ])
    if (material[`get${key}Texture`]())
      infos.push(material[`get${key}TextureInfo`]());
  const primitives = doc
    .getRoot()
    .listMeshes()
    .flatMap((m) => m.listPrimitives())
    .filter(
      (p) => p.getMaterial() === material && p.getAttribute('TEXCOORD_0'),
    );
  if (!infos.length) {
    for (const p of primitives) p.setAttribute('TEXCOORD_0', null);
    continue;
  }
  if (!primitives.length) continue;
  let minU = Infinity,
    minV = Infinity,
    maxU = -Infinity,
    maxV = -Infinity;
  for (const p of primitives) {
    const a = p.getAttribute('TEXCOORD_0').getArray();
    for (let i = 0; i < a.length; i += 2) {
      minU = Math.min(minU, a[i]);
      maxU = Math.max(maxU, a[i]);
      minV = Math.min(minV, a[i + 1]);
      maxV = Math.max(maxV, a[i + 1]);
    }
  }
  const du = Math.max(maxU - minU, 1),
    dv = Math.max(maxV - minV, 1);
  for (const p of primitives) {
    const uv = p.getAttribute('TEXCOORD_0').clone(),
      a = uv.getArray().slice();
    for (let i = 0; i < a.length; i += 2) {
      a[i] = (a[i] - minU) / du;
      a[i + 1] = (a[i + 1] - minV) / dv;
    }
    uv.setArray(a);
    p.setAttribute('TEXCOORD_0', uv);
  }
  for (const info of infos)
    info.setExtension(
      'KHR_texture_transform',
      extension.createTransform().setOffset([minU, minV]).setScale([du, dv]),
    );
}
await doc.transform(
  dedup(),
  weld(),
  meshopt({
    encoder: MeshoptEncoder,
    level: 'high',
    quantizePosition: 16,
    quantizeNormal: 10,
    quantizeTexcoord: 16,
  }),
);
await io.write('public/villa-v2.glb', doc);
console.log('V2 model optimized without mesh simplification.');
