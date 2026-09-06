import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, weld, join, meshopt } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
await MeshoptEncoder.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({
    'meshopt.encoder': MeshoptEncoder,
    'meshopt.decoder': MeshoptDecoder,
  });
const source = process.argv[2];
if (!source) throw Error('Provide the Blender web GLB export path.');
const doc = await io.read(source);
await doc.transform(
  dedup(),
  join({ keepMeshes: true }),
  weld(),
  meshopt({
    encoder: MeshoptEncoder,
    level: 'medium',
    quantizePosition: 16,
    quantizeNormal: 10,
  }),
);
await io.write('public/villa.glb', doc);
console.log('Optimized villa.glb written.');
