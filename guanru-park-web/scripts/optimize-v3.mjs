import { NodeIO } from '@gltf-transform/core';
import {
  ALL_EXTENSIONS,
  KHRTextureTransform,
} from '@gltf-transform/extensions';
import { dedup, weld, join, meshopt, prune } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
await MeshoptEncoder.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({
    'meshopt.encoder': MeshoptEncoder,
    'meshopt.decoder': MeshoptDecoder,
  });
const source = process.argv[2];
if (!source) throw Error('Provide export directory');
const out = 'public/assets-v3';
await fs.mkdir(out + '/textures/high', { recursive: true });
const manifest = {
  version: '3.0',
  assets: [],
  textureTiers: { high: 2048, standard: 1024 },
  lights: '/assets-v3/lights.json',
  mirrors: '/assets-v3/mirrors.json',
  rooms: '/assets-v3/rooms.json',
  lightmaps: {},
};
for (const floor of ['B1', '1F', '2F', '3F', 'Roof', 'Site']) {
  const doc = await io.read(path.join(source, floor + '.glb'));
  for (const m of doc.getRoot().listMaterials())
    if (m.getName().startsWith('V3 ' + floor + ' floor '))
      m.setExtras({ lightmapFloor: floor });
  await doc.transform(dedup(), join({ keepMeshes: true }), weld());
  const ext = doc.createExtension(KHRTextureTransform);
  for (const material of doc.getRoot().listMaterials()) {
    const infos = [
      'BaseColor',
      'Normal',
      'MetallicRoughness',
      'Occlusion',
      'Emissive',
    ]
      .filter((k) => material[`get${k}Texture`]())
      .map((k) => material[`get${k}TextureInfo`]());
    const primitives = doc
      .getRoot()
      .listMeshes()
      .flatMap((m) => m.listPrimitives())
      .filter(
        (p) => p.getMaterial() === material && p.getAttribute('TEXCOORD_0'),
      );
    if (!infos.length) continue;
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
    if (!Number.isFinite(minU)) continue;
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
        ext.createTransform().setOffset([minU, minV]).setScale([du, dv]),
      );
  }
  await doc.transform(
    dedup(),
    weld(),
    prune({ keepAttributes: true, keepExtras: true }),
    meshopt({
      encoder: MeshoptEncoder,
      level: 'high',
      quantizePosition: 16,
      quantizeNormal: 12,
      quantizeTexcoord: 16,
    }),
  );
  for (const tex of doc.getRoot().listTextures()) {
    const bytes = tex.getImage();
    const sha = createHash('sha256').update(bytes).digest('hex').slice(0, 20);
    tex.setName(sha + (tex.getMimeType() === 'image/png' ? '.png' : '.jpg'));
    tex.setURI('textures/high/' + tex.getName());
  }
  doc
    .getRoot()
    .listBuffers()
    .forEach((b, i) => b.setURI(floor + (i ? '_' + i : '') + '.bin'));
  await io.write(out + '/' + floor + '.gltf', doc);
  const stat = await fs.stat(out + '/' + floor + '.bin');
  if (stat.size > 25 * 1024 * 1024) throw Error(floor + ' exceeds asset cap');
  manifest.assets.push({
    floor,
    url: '/assets-v3/' + floor + '.gltf',
    bytes: stat.size,
  });
  console.log(floor, stat.size);
}
await fs.mkdir(out + '/lightmaps', { recursive: true });
for (const floor of ['B1', '1F', '2F', '3F']) {
  await fs.copyFile(
    path.join(source, 'lightmaps', floor + '.hdr'),
    out + '/lightmaps/' + floor + '.hdr',
  );
  manifest.lightmaps[floor] = '/assets-v3/lightmaps/' + floor + '.hdr';
}
await fs.copyFile(path.join(source, 'lights.json'), out + '/lights.json');
await fs.copyFile(
  path.join(source, '../room_schedule.json'),
  out + '/rooms.json',
);
await fs.writeFile(out + '/manifest.json', JSON.stringify(manifest, null, 2));

await fs.copyFile(path.join(source, 'mirrors.json'), out + '/mirrors.json');
