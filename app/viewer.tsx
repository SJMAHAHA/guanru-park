'use client';
import { useEffect, useRef, type RefObject } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { SMAAPass } from 'three/addons/postprocessing/SMAAPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';
import { Reflector } from 'three/addons/objects/Reflector.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import {
  applyGroups,
  INTERIORS,
  LEVELS,
  PRESETS,
  ROOMS,
  type Options,
} from './model-state';
export type ViewerAPI = {
  zoom: (factor: number) => void;
  benchmark: () => void;
};
export type PerformanceStats = {
  quality: string;
  gpu: string;
  browser: string;
  loadSeconds: number;
  fps: number;
  renderMs: number;
  triangles: number;
  calls: number;
  viewport: string;
};
type Fixture = {
  floor: string;
  room: string;
  position: [number, number, number];
  power: number;
  range: number;
};
type MirrorPlane = {
  floor: string;
  position: [number, number, number];
  normal: [number, number, number];
  size: [number, number];
};
type AssetManifest = {
  version: string;
  assets: { floor: string; url: string; bytes: number }[];
  lights: string;
  lightmaps: Record<string, string>;
  mirrors: string;
};
export type LabelPosition = { id: string; name: string; x: number; y: number };
export default function Viewer({
  options,
  apiRef,
  onProgress,
  onReady,
  onError,
  onLabels,
  onStats,
}: {
  options: Options;
  apiRef: RefObject<ViewerAPI | null>;
  onProgress: (n: number) => void;
  onReady: () => void;
  onError: (s: string) => void;
  onLabels: (labels: LabelPosition[]) => void;
  onStats: (stats: PerformanceStats) => void;
}) {
  const host = useRef<HTMLDivElement>(null),
    apply = useRef<((o: Options) => void) | null>(null),
    latest = useRef(options),
    callbacks = useRef({ onProgress, onReady, onError, onLabels, onStats });
  useEffect(() => {
    latest.current = options;
  }, [options]);
  useEffect(() => {
    callbacks.current = { onProgress, onReady, onError, onLabels, onStats };
  }, [onProgress, onReady, onError, onLabels, onStats]);
  useEffect(() => {
    const el = host.current;
    if (!el) return;
    let alive = true,
      frame = 0,
      dirty = true,
      model: THREE.Group | undefined,
      lastCamera = '',
      lastVisibility = '',
      lastLight = '',
      lastLabels = '',
      lastLabelsAt = 0;
    const startedAt = performance.now();
    let loadedAt = 0,
      lastQuality = '',
      qualityEpoch = 0,
      benchmarkUntil = 0;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#eaf0f0');
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        powerPreference: 'high-performance',
      });
    } catch {
      callbacks.current.onError(
        '当前浏览器无法启动三维显示，请开启硬件加速或换用支持 WebGL 的浏览器。',
      );
      return;
    }
    renderer.setPixelRatio(
      Math.min(
        window.devicePixelRatio,
        latest.current.quality === 'high' ? 2 : 1.5,
      ),
    );
    renderer.setSize(el.clientWidth, el.clientHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    renderer.shadowMap.autoUpdate = false;
    renderer.localClippingEnabled = true;
    renderer.transmissionResolutionScale = 0.5;
    const gl = renderer.getContext(),
      gpuInfo = gl.getExtension('WEBGL_debug_renderer_info');
    const gpu = String(
      gpuInfo
        ? gl.getParameter(gpuInfo.UNMASKED_RENDERER_WEBGL)
        : gl.getParameter(gl.RENDERER),
    );
    el.appendChild(renderer.domElement);
    renderer.domElement.tabIndex = 0;
    renderer.domElement.setAttribute(
      'aria-label',
      'Guanru Park 3.0 三维模型。拖动旋转，双指或滚轮缩放，右键或方向键平移。',
    );
    const perspective = new THREE.PerspectiveCamera(38, 1, 0.045, 600),
      ortho = new THREE.OrthographicCamera(-35, 35, 35, -35, 0.045, 600);
    let camera: THREE.PerspectiveCamera | THREE.OrthographicCamera =
      perspective;
    const controls = new OrbitControls<
      THREE.PerspectiveCamera | THREE.OrthographicCamera
    >(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.1;
    controls.minDistance = 0.6;
    controls.maxDistance = 240;
    controls.minZoom = 0.45;
    controls.maxZoom = 12;
    controls.maxPolarAngle = Math.PI * 0.49;
    controls.autoRotateSpeed = 0.5;
    controls.listenToKeyEvents(renderer.domElement);
    controls.addEventListener('change', () => {
      dirty = true;
    });
    const hemisphere = new THREE.HemisphereLight(0xdcebf5, 0x969c8e, 2);
    scene.add(hemisphere);
    const sun = new THREE.DirectionalLight(0xfff3df, 3);
    sun.position.set(35, 65, -35);
    sun.castShadow = true;
    sun.shadow.mapSize.set(4096, 4096);
    Object.assign(sun.shadow.camera, {
      left: -49,
      right: 49,
      top: 49,
      bottom: -49,
      near: 1,
      far: 180,
    });
    sun.shadow.camera.updateProjectionMatrix();
    sun.shadow.normalBias = 0.018;
    sun.shadow.bias = -0.00015;
    scene.add(sun);
    const pmrem = new THREE.PMREMGenerator(renderer),
      roomEnvironment = new RoomEnvironment(),
      environment = pmrem.fromScene(roomEnvironment, 0.04);
    scene.environment = environment.texture;
    scene.environmentIntensity = 0.4;
    roomEnvironment.dispose();
    pmrem.dispose();
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(500, 500),
      new THREE.MeshStandardMaterial({ color: 0xd9e1df, roughness: 0.95 }),
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.335;
    ground.receiveShadow = true;
    scene.add(ground);
    // A bounded pool follows the closest real fixtures; no 146-light shader variant.
    let fixtures: Fixture[] = [];
    const fixtureLights = Array.from({ length: 8 }, () => {
      const light = new THREE.PointLight(0xffd8af, 0, 6, 2);
      scene.add(light);
      return light;
    });
    let lastFixtureSelection = 0;
    const updateFixtures = () => {
      const o = latest.current;
      const near = fixtures
        .filter(
          (f) =>
            (o.floor === 'all' || o.floor === f.floor) &&
            (!o.cut || o.explode || f.position[1] <= o.cutHeight),
        )
        .map((f) => ({
          f,
          p: new THREE.Vector3(...f.position).add(
            new THREE.Vector3(
              0,
              o.explode && o.floor === 'all'
                ? (LEVELS[f.floor] / 3.15) * 5.5
                : 0,
              0,
            ),
          ),
        }))
        .sort(
          (a, b) =>
            a.p.distanceToSquared(camera.position) -
            b.p.distanceToSquared(camera.position),
        );
      fixtureLights.forEach((l, i) => {
        const v = near[i];
        l.visible = !!v;
        if (v) {
          l.position.copy(v.p);
          l.distance = v.f.range;
          l.intensity = (o.evening ? 1.4 : 0.7) * v.f.power;
        }
      });
    };
    const cutPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), 14),
      materials = new Set<THREE.MeshStandardMaterial>();
    const renderTarget = new THREE.WebGLRenderTarget(
      el.clientWidth,
      el.clientHeight,
      { type: THREE.HalfFloatType, samples: 0 },
    );
    const composer = new EffectComposer(renderer, renderTarget);
    const renderPass = new RenderPass(scene, camera);
    const aoPass = new GTAOPass(scene, camera, el.clientWidth, el.clientHeight);
    aoPass.blendIntensity = 0.35;
    aoPass.updateGtaoMaterial({
      radius: 0.24,
      thickness: 0.1,
      distanceFallOff: 1,
      samples: 12,
    });
    const outputPass = new OutputPass();
    const antialiasPass = new SMAAPass();
    composer.addPass(renderPass);
    composer.addPass(aoPass);
    composer.addPass(outputPass);
    composer.addPass(antialiasPass);
    // Transparent panes must not become opaque occluders in the AO normal/depth pass.
    const transparentMeshes = new Set<THREE.Mesh>();
    const mirror = new Reflector(new THREE.PlaneGeometry(1, 1), {
      textureWidth: 512,
      textureHeight: 512,
      clipBias: 0.003,
      color: 0xc4c9c9,
      multisample: 0,
    });
    mirror.visible = false;
    scene.add(mirror);
    transparentMeshes.add(mirror);
    let mirrorPlanes: MirrorPlane[] = [];
    const updateMirror = () => {
      const o = latest.current;
      mirror.visible = false;
      if (
        (o.view !== 'bath' && o.focus !== 'master-bath') ||
        !o.furniture ||
        o.cut ||
        o.explode ||
        o.reveal
      )
        return;
      const near = mirrorPlanes
        .filter((m) => o.floor === 'all' || m.floor === o.floor)
        .map((m) => ({
          m,
          d: camera.position.distanceToSquared(
            new THREE.Vector3(...m.position),
          ),
        }))
        .sort((a, b) => a.d - b.d)[0];
      if (!near || near.d > 144) return;
      const m = near.m;
      mirror.position.fromArray(m.position);
      mirror.scale.set(m.size[0], m.size[1], 1);
      mirror.lookAt(
        new THREE.Vector3(...m.position).add(new THREE.Vector3(...m.normal)),
      );
      mirror.visible = true;
    };
    const baseAoRender = aoPass.render.bind(aoPass);
    aoPass.render = (r, w, read, delta, mask) => {
      const hidden: THREE.Mesh[] = [];
      transparentMeshes.forEach((m) => {
        if (m.visible) {
          hidden.push(m);
          m.visible = false;
        }
      });
      try {
        baseAoRender(r, w, read, delta, mask);
      } finally {
        hidden.forEach((m) => (m.visible = true));
      }
    };
    const textureSlots = new Map<
      THREE.MeshStandardMaterial,
      Map<string, THREE.Texture>
    >();
    const loadedTextureVariants = new Map<string, THREE.Texture>();
    const extraTextures = new Set<THREE.Texture>();
    const bitmapPromises = new Map<string, Promise<ImageBitmap>>();
    const aborter = new AbortController();
    const applyQualityTextures = async (quality: 'high' | 'standard') => {
      const epoch = ++qualityEpoch;
      try {
        await Promise.all(
          [...textureSlots].flatMap(([m, slots]) =>
            [...slots].map(async ([slot, original]) => {
              if (!/^[a-f0-9]{20}\.(jpg|png)$/.test(original.name)) return;
              const key = original.uuid + quality;
              let tex = loadedTextureVariants.get(key);
              if (!tex) {
                if (quality === 'high') tex = original;
                else {
                  const url = '/assets-v3/textures/standard/' + original.name;
                  if (!bitmapPromises.has(url))
                    bitmapPromises.set(
                      url,
                      new THREE.ImageBitmapLoader()
                        .setOptions({ imageOrientation: 'none' })
                        .loadAsync(url),
                    );
                  const image = await bitmapPromises.get(url)!;
                  if (!image) throw Error('Missing texture bitmap ' + url);
                  tex = original.clone();
                  tex.source = new THREE.Source(image);
                  tex.needsUpdate = true;
                  extraTextures.add(tex);
                }
                loadedTextureVariants.set(key, tex);
              }
              if (alive && epoch === qualityEpoch) {
                (m as unknown as Record<string, unknown>)[slot] = tex;
                m.needsUpdate = true;
              }
            }),
          ),
        );
        if (alive && epoch === qualityEpoch) dirty = true;
      } catch {
        if (alive)
          callbacks.current.onError('画质资源未能加载，请检查网络后重新加载。');
      }
    };
    const setSize = () => {
      const w = el.clientWidth,
        h = el.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h);
      composer.setSize(w, h);
      aoPass.setSize(
        Math.max(1, Math.floor(w * renderer.getPixelRatio() * 0.5)),
        Math.max(1, Math.floor(h * renderer.getPixelRatio() * 0.5)),
      );
      perspective.aspect = w / h;
      perspective.updateProjectionMatrix();
      const half = 31 * Math.max(1, h / w);
      ortho.left = (-half * w) / h;
      ortho.right = (half * w) / h;
      ortho.top = half;
      ortho.bottom = -half;
      ortho.updateProjectionMatrix();
      dirty = true;
    };
    const resize = new ResizeObserver(setSize);
    resize.observe(el);
    const positionLabels = () => {
      const o = latest.current;
      if (!o.labels || o.floor === 'all' || !model || INTERIORS.has(o.view)) {
        if (lastLabels !== '[]') {
          lastLabels = '[]';
          callbacks.current.onLabels([]);
        }
        return;
      }
      const labels: LabelPosition[] = [];
      for (const r of ROOMS.filter((r) => r.floor === o.floor)) {
        const v = new THREE.Vector3(
          r.position[0],
          r.position[1] + 2.88,
          r.position[2],
        ).project(camera);
        if (v.z > -1 && v.z < 1 && Math.abs(v.x) < 0.94 && Math.abs(v.y) < 0.88)
          labels.push({
            id: r.id,
            name: r.name,
            x: Math.round(((v.x + 1) * el.clientWidth) / 2),
            y: Math.round(((1 - v.y) * el.clientHeight) / 2),
          });
      }
      const key = JSON.stringify(labels);
      if (key !== lastLabels) {
        lastLabels = key;
        callbacks.current.onLabels(labels);
      }
    };
    const applyOptions = (o: Options) => {
      if (!alive) return;
      const visibilityKey = JSON.stringify([
        o.floor,
        o.furniture,
        o.explode,
        o.reveal,
        o.cut,
        o.cutHeight,
      ]);
      if (model && lastVisibility !== visibilityKey) {
        applyGroups(model, o);
        cutPlane.constant = o.cutHeight;
        for (const m of materials) {
          const enable = o.cut && !o.explode;
          if ((m.clippingPlanes?.length ?? 0) !== (enable ? 1 : 0))
            m.needsUpdate = true;
          m.clippingPlanes = enable ? [cutPlane] : [];
          m.clipShadows = true;
        }
        renderer.shadowMap.needsUpdate = true;
        lastVisibility = visibilityKey;
      }
      const useBaked =
        o.floor === 'all' && !o.cut && !o.explode && !o.reveal && o.furniture;
      materials.forEach((m) => {
        if (m.lightMap)
          m.lightMapIntensity = useBaked ? (o.evening ? 0.22 : 0.65) : 0;
      });
      aoPass.normalMaterial.clippingPlanes =
        o.cut && !o.explode ? [cutPlane] : [];
      aoPass.normalMaterial.needsUpdate = true;
      if (lastQuality !== o.quality) {
        lastQuality = o.quality;
        const high = o.quality === 'high';
        mirror.getRenderTarget().setSize(high ? 512 : 256, high ? 512 : 256);
        renderer.setPixelRatio(
          Math.min(window.devicePixelRatio, high ? 2 : 1.5),
        );
        composer.setPixelRatio(renderer.getPixelRatio());
        aoPass.enabled = high;
        const size = high ? 4096 : 2048;
        sun.shadow.mapSize.set(size, size);
        sun.shadow.map?.dispose();
        sun.shadow.map = null;
        renderer.shadowMap.needsUpdate = true;
        setSize();
        void applyQualityTextures(o.quality);
      }
      ground.visible = o.floor === 'all';
      controls.autoRotate =
        o.rotate && o.view !== 'plan' && !INTERIORS.has(o.view);
      const lightKey = JSON.stringify([
        o.evening,
        o.floor,
        o.explode,
        o.cut,
        o.cutHeight,
      ]);
      if (lastLight !== lightKey) {
        hemisphere.intensity = o.evening ? 0.3 : 1.1;
        sun.intensity = o.evening ? 0.42 : 3;
        sun.color.set(o.evening ? 0x8aa6d3 : 0xfff3df);
        scene.background = new THREE.Color(o.evening ? '#142b42' : '#eaf0f0');
        scene.environmentIntensity = o.evening ? 0.28 : 0.65;
        renderer.toneMappingExposure = o.evening ? 1.05 : 0.85;
        updateFixtures();
        for (const m of materials) {
          if (m.name === 'Light warm')
            m.emissiveIntensity = o.evening ? 5 : 1.8;
        }
        renderer.shadowMap.needsUpdate = true;
        lastLight = lightKey;
      }
      const cameraKey = JSON.stringify([
        o.floor,
        o.view,
        o.reset,
        o.explode,
        o.focus,
      ]);
      if (lastCamera !== cameraKey) {
        const focused = ROOMS.find((r) => r.id === o.focus),
          interior = INTERIORS.has(o.view) && !focused;
        camera = o.view === 'plan' && !focused ? ortho : perspective;
        controls.object = camera;
        controls.enableRotate = camera !== ortho;
        controls.maxPolarAngle = interior ? Math.PI * 0.82 : Math.PI * 0.49;
        controls.minDistance = interior ? 0.3 : 2;
        controls.maxDistance = interior ? 35 : 240;
        camera.up.set(0, camera === ortho ? 0 : 1, camera === ortho ? -1 : 0);
        perspective.fov = 38;
        if (focused) {
          const [x, y, z] = focused.position;
          perspective.position.set(x + 5, y + 7, z + 6);
          controls.target.set(x, y + 0.6, z);
        } else if (camera === ortho) {
          ortho.position.set(0, 110, 0);
          ortho.zoom = 1;
          ortho.updateProjectionMatrix();
          controls.target.set(0, LEVELS[o.floor] ?? 0, 0);
        } else {
          const p = PRESETS[o.view === 'plan' ? 'aerial' : o.view];
          perspective.fov = p.fov ?? 38;
          const factor =
            interior || o.view === 'pool'
              ? 1
              : Math.max(1, 0.95 / (el.clientWidth / el.clientHeight));
          perspective.position.fromArray(p.position).multiplyScalar(factor);
          controls.target.fromArray(p.target);
          if (o.floor !== 'all') controls.target.y = LEVELS[o.floor] + 1.1;
          if (o.explode && o.floor === 'all') {
            perspective.position.set(85, 70, -110);
            controls.target.set(0, 18, 0);
          }
        }
        perspective.updateProjectionMatrix();
        camera.lookAt(controls.target);
        controls.update();
        lastCamera = cameraKey;
      }
      renderPass.camera = camera;
      aoPass.camera = camera;
      aoPass.gtaoMaterial.defines.PERSPECTIVE_CAMERA =
        camera === perspective ? 1 : 0;
      aoPass.gtaoMaterial.needsUpdate = true;
      updateFixtures();
      dirty = true;
      positionLabels();
    };
    apply.current = applyOptions;
    setSize();
    applyOptions(latest.current);
    apiRef.current = {
      benchmark() {
        benchmarkUntil = performance.now() + 5000;
        sampleAt = performance.now();
        renderedFrames = 0;
        renderTotal = 0;
        frameIntervals = [];
        lastRendered = 0;
      },
      zoom(factor) {
        if (camera === ortho) {
          ortho.zoom = THREE.MathUtils.clamp(
            ortho.zoom / factor,
            controls.minZoom,
            controls.maxZoom,
          );
          ortho.updateProjectionMatrix();
        } else
          perspective.position
            .sub(controls.target)
            .multiplyScalar(factor)
            .add(controls.target);
        controls.update();
        dirty = true;
      },
    };
    let lastTime = performance.now(),
      sampleAt = lastTime,
      renderedFrames = 0,
      renderTotal = 0,
      lastRendered = 0;
    let frameIntervals: number[] = [];
    const draw = () => {
      updateMirror();
      renderer.info.autoReset = false;
      renderer.info.reset();
      if (latest.current.quality === 'high') composer.render();
      else renderer.render(scene, camera);
    };
    const animate = (now: number) => {
      if (!alive) return;
      frame = requestAnimationFrame(animate);
      const changed = controls.update(Math.min((now - lastTime) / 1000, 0.1));
      lastTime = now;
      if (dirty || changed || now < benchmarkUntil) {
        if (now - lastFixtureSelection > 500) {
          updateFixtures();
          lastFixtureSelection = now;
        }
        const begin = performance.now();
        try {
          draw();
        } catch (error) {
          console.error('V3 render', error);
          cancelAnimationFrame(frame);
          callbacks.current.onError('三维显示出现错误，请重新加载。');
          return;
        }
        renderTotal += performance.now() - begin;
        renderedFrames++;
        if (lastRendered && now - lastRendered < 500)
          frameIntervals.push(now - lastRendered);
        lastRendered = now;
        if (now - sampleAt > 1000) {
          callbacks.current.onStats({
            quality: latest.current.quality,
            gpu,
            browser: navigator.userAgent,
            loadSeconds: loadedAt ? (loadedAt - startedAt) / 1000 : 0,
            fps: frameIntervals.length
              ? 1000 /
                (frameIntervals.reduce((a, b) => a + b, 0) /
                  frameIntervals.length)
              : 0,
            renderMs: renderTotal / Math.max(renderedFrames, 1),
            triangles: renderer.info.render.triangles,
            calls: renderer.info.render.calls,
            viewport:
              el.clientWidth +
              ' × ' +
              el.clientHeight +
              ' @ ' +
              renderer.getPixelRatio().toFixed(2),
          });
          sampleAt = now;
          renderedFrames = 0;
          renderTotal = 0;
          frameIntervals = [];
        }
        dirty = false;
        if (now - lastLabelsAt > 100) {
          positionLabels();
          lastLabelsAt = now;
        }
      }
    };
    frame = requestAnimationFrame(animate);
    const lost = (event: Event) => {
      event.preventDefault();
      callbacks.current.onError('三维显示已暂停，请点击重新加载。');
    };
    renderer.domElement.addEventListener('webglcontextlost', lost);
    const getJSON = async <T,>(url: string): Promise<T> => {
      const res = await fetch(url, { signal: aborter.signal });
      if (!res.ok) throw Error(url + ': ' + res.status);
      return res.json();
    };
    const disposeModel = (root: THREE.Object3D) =>
      root.traverse((n) => {
        if (n instanceof THREE.Mesh) {
          n.geometry.dispose();
          (Array.isArray(n.material) ? n.material : [n.material]).forEach(
            (m) => {
              Object.values(m).forEach((v) => {
                if (v instanceof THREE.Texture) v.dispose();
              });
              m.dispose();
            },
          );
        }
      });
    void (async () => {
      const manifest = await getJSON<AssetManifest>('/assets-v3/manifest.json');
      fixtures = await getJSON<Fixture[]>(manifest.lights);
      mirrorPlanes = await getJSON<MirrorPlane[]>(manifest.mirrors);
      const manager = new THREE.LoadingManager();
      // Shared image responses across floor files; meshes and materials stay independently grouped.
      THREE.Cache.enabled = false;
      const loader = new GLTFLoader(manager).setMeshoptDecoder(MeshoptDecoder);
      const lightmaps: Record<string, THREE.DataTexture> = {};
      await Promise.all(
        Object.entries(manifest.lightmaps).map(async ([floor, url]) => {
          const t = await new HDRLoader().loadAsync(url);
          t.flipY = false;
          t.channel = 1;
          lightmaps[floor] = t;
          extraTextures.add(t);
        }),
      );
      const root = new THREE.Group();
      let completed = 0;
      const sharedMaterials = new Map<string, THREE.MeshStandardMaterial>();
      for (const asset of manifest.assets) {
        const gltf = await loader.loadAsync(asset.url);
        if (!alive) {
          disposeModel(gltf.scene);
          disposeModel(root);
          return;
        }
        const anisotropy = Math.min(
          16,
          renderer.capabilities.getMaxAnisotropy(),
        );
        gltf.scene.traverse((n) => {
          if (!(n instanceof THREE.Mesh)) return;
          n.castShadow = true;
          n.receiveShadow = true;
          const input = (
            Array.isArray(n.material) ? n.material : [n.material]
          ) as THREE.MeshStandardMaterial[];
          const output = input.map((original) => {
            let m = sharedMaterials.get(asset.floor + original.name);
            if (!m) {
              m = original;
              sharedMaterials.set(asset.floor + m.name, m);
              materials.add(m);
              const slots = new Map<string, THREE.Texture>();
              for (const slot of [
                'map',
                'normalMap',
                'roughnessMap',
                'metalnessMap',
              ] as const) {
                const t = m[slot];
                if (t) {
                  t.anisotropy = anisotropy;
                  t.needsUpdate = true;
                  slots.set(slot, t);
                }
              }
              textureSlots.set(m, slots);
              if (m.name.startsWith('V3 ' + asset.floor + ' floor ')) {
                if (!n.geometry.getAttribute('uv1'))
                  throw Error('Missing baked UV2 on ' + n.name);
                m.lightMap = lightmaps[asset.floor];
                m.lightMapIntensity = 0.65;
              }
              if (['Clear glazing', 'Glassware'].includes(m.name)) {
                const physical = m as THREE.MeshPhysicalMaterial;
                physical.color.set(0xffffff);
                physical.roughness = 0.018;
                physical.metalness = 0;
                physical.transmission = 1;
                physical.thickness = 0.012;
                physical.ior = 1.46;
                physical.transparent = false;
                physical.opacity = 1;
                physical.depthWrite = true;
                physical.envMapIntensity = 0.4;
                physical.side = THREE.FrontSide;
              }
              if (m.name === 'Water') {
                const physical = m as THREE.MeshPhysicalMaterial;
                physical.color.set(0x8fc5bd);
                physical.transmission = 0.72;
                physical.thickness = 0.3;
                physical.ior = 1.333;
                physical.roughness = 0.1;
                physical.metalness = 0;
                physical.attenuationColor.set(0x438a88);
                physical.attenuationDistance = 3;
                physical.normalScale.set(0.14, 0.14);
                physical.envMapIntensity = 1.0;
              }
            } else if (m !== original) original.dispose();
            if (['Clear glazing', 'Glassware', 'Water'].includes(m.name)) {
              n.castShadow = false;
              transparentMeshes.add(n);
            }
            return m;
          });
          n.material = Array.isArray(n.material) ? output : output[0];
        });
        root.add(gltf.scene);
        completed++;
        callbacks.current.onProgress(
          Math.round((completed / manifest.assets.length) * 94),
        );
      }
      if (!alive) {
        disposeModel(root);
        return;
      }
      model = root;
      scene.add(model);
      lastVisibility = '';
      lastLight = '';
      lastQuality = '';
      applyOptions(latest.current);
      await applyQualityTextures(latest.current.quality);
      if (!alive) return;
      await renderer.compileAsync(scene, camera);
      draw();
      loadedAt = performance.now();
      dirty = true;
      callbacks.current.onReady();
    })().catch((e) => {
      if (alive) {
        console.error('V3 assets', e);
        callbacks.current.onError('模型或材质未能加载，请检查网络后重试。');
      }
    });
    return () => {
      alive = false;
      aborter.abort();
      qualityEpoch++;
      apply.current = null;
      apiRef.current = null;
      cancelAnimationFrame(frame);
      resize.disconnect();
      controls.dispose();
      renderer.domElement.removeEventListener('webglcontextlost', lost);
      const geometries = new Set<THREE.BufferGeometry>(),
        textures = new Set<THREE.Texture>();
      scene.traverse((n) => {
        if (n instanceof THREE.Mesh) {
          geometries.add(n.geometry);
          for (const m of (Array.isArray(n.material)
            ? n.material
            : [n.material]) as THREE.MeshStandardMaterial[]) {
            for (const value of Object.values(m))
              if (value instanceof THREE.Texture) textures.add(value);
            m.dispose();
          }
        }
      });
      geometries.forEach((g) => g.dispose());
      textures.forEach((t) => t.dispose());
      extraTextures.forEach((t) => t.dispose());
      composer.dispose();
      aoPass.dispose();
      outputPass.dispose();
      antialiasPass.dispose();
      mirror.dispose();
      environment.dispose();
      sun.shadow.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, [apiRef]);
  useEffect(() => {
    apply.current?.(options);
  }, [options]);
  return <div className="scene-host" ref={host} />;
}
