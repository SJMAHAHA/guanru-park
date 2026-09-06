'use client';
import { useEffect, useRef, type RefObject } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import {
  applyGroups,
  INTERIORS,
  LEVELS,
  PRESETS,
  ROOMS,
  type Options,
} from './model-state';
export type ViewerAPI = { zoom: (factor: number) => void };
export type LabelPosition = { id: string; name: string; x: number; y: number };
export default function Viewer({
  options,
  apiRef,
  onProgress,
  onReady,
  onError,
  onLabels,
}: {
  options: Options;
  apiRef: RefObject<ViewerAPI | null>;
  onProgress: (n: number) => void;
  onReady: () => void;
  onError: (s: string) => void;
  onLabels: (labels: LabelPosition[]) => void;
}) {
  const host = useRef<HTMLDivElement>(null),
    apply = useRef<((o: Options) => void) | null>(null),
    latest = useRef(options),
    callbacks = useRef({ onProgress, onReady, onError, onLabels });
  useEffect(() => {
    latest.current = options;
  }, [options]);
  useEffect(() => {
    callbacks.current = { onProgress, onReady, onError, onLabels };
  }, [onProgress, onReady, onError, onLabels]);
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
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    renderer.setSize(el.clientWidth, el.clientHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    renderer.shadowMap.autoUpdate = false;
    renderer.localClippingEnabled = true;
    el.appendChild(renderer.domElement);
    renderer.domElement.tabIndex = 0;
    renderer.domElement.setAttribute(
      'aria-label',
      'Guanru Park 2.0 三维模型。拖动旋转，双指或滚轮缩放，右键或方向键平移。',
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
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, {
      left: -49,
      right: 49,
      top: 49,
      bottom: -49,
      near: 1,
      far: 180,
    });
    sun.shadow.camera.updateProjectionMatrix();
    sun.shadow.normalBias = 0.035;
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
    const warmLights: {
      light: THREE.PointLight;
      floor: string;
      base: number;
    }[] = [];
    for (const roomId of [
      'living',
      'family',
      'kitchen',
      'master',
      'guest',
      'indoor-pool',
      'pavilion',
    ]) {
      const r = ROOMS.find((r) => r.id === roomId)!;
      const light = new THREE.PointLight(0xffc17c, 0, 15, 2);
      light.position.set(r.position[0], r.position[1] + 2.5, r.position[2]);
      scene.add(light);
      warmLights.push({ light, floor: r.floor, base: light.position.y });
    }
    const cutPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), 14),
      materials = new Set<THREE.MeshStandardMaterial>();
    const setSize = () => {
      const w = el.clientWidth,
        h = el.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h);
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
        hemisphere.intensity = o.evening ? 0.48 : 2;
        sun.intensity = o.evening ? 0.42 : 3;
        sun.color.set(o.evening ? 0x8aa6d3 : 0xfff3df);
        scene.background = new THREE.Color(o.evening ? '#142b42' : '#eaf0f0');
        scene.environmentIntensity = o.evening ? 0.16 : 0.4;
        renderer.toneMappingExposure = o.evening ? 1.2 : 1.05;
        for (const { light, floor, base } of warmLights) {
          light.position.y =
            base +
            (o.explode && o.floor === 'all' ? (LEVELS[floor] / 3.15) * 5.5 : 0);
          light.visible =
            (o.floor === 'all' || o.floor === floor) &&
            (!o.cut || o.explode || light.position.y <= o.cutHeight);
          light.intensity = o.evening ? 95 : 9;
        }
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
      dirty = true;
      positionLabels();
    };
    apply.current = applyOptions;
    setSize();
    applyOptions(latest.current);
    apiRef.current = {
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
    let lastTime = performance.now();
    const animate = (now: number) => {
      if (!alive) return;
      frame = requestAnimationFrame(animate);
      const changed = controls.update(Math.min((now - lastTime) / 1000, 0.1));
      lastTime = now;
      if (dirty || changed) {
        renderer.render(scene, camera);
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
    new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).load(
      '/villa-v2.glb',
      (gltf) => {
        if (!alive) {
          gltf.scene.traverse((n) => {
            if (n instanceof THREE.Mesh) {
              n.geometry.dispose();
              (Array.isArray(n.material) ? n.material : [n.material]).forEach(
                (m) => m.dispose(),
              );
            }
          });
          return;
        }
        model = gltf.scene;
        const anisotropy = Math.min(
          8,
          renderer.capabilities.getMaxAnisotropy(),
        );
        model.traverse((n) => {
          if (n instanceof THREE.Mesh) {
            n.castShadow = true;
            n.receiveShadow = true;
            for (const m of (Array.isArray(n.material)
              ? n.material
              : [n.material]) as THREE.MeshStandardMaterial[]) {
              materials.add(m);
              for (const t of [
                m.map,
                m.normalMap,
                m.roughnessMap,
                m.metalnessMap,
              ])
                if (t) {
                  t.anisotropy = anisotropy;
                  t.needsUpdate = true;
                }
              if (['Clear glazing', 'Glassware'].includes(m.name)) {
                m.transparent = true;
                m.opacity = m.name === 'Clear glazing' ? 0.18 : 0.28;
                m.depthWrite = false;
                n.castShadow = false;
                m.side = THREE.DoubleSide;
              }
              if (m.name === 'Water') {
                n.castShadow = false;
                m.normalScale.set(0.1, 0.1);
              }
            }
          }
        });
        scene.add(model);
        lastVisibility = '';
        lastLight = '';
        applyOptions(latest.current);
        renderer.render(scene, camera);
        callbacks.current.onReady();
      },
      (xhr) => {
        if (alive && xhr.total)
          callbacks.current.onProgress(
            Math.min(99, Math.round((xhr.loaded / xhr.total) * 100)),
          );
      },
      () => {
        if (alive)
          callbacks.current.onError(
            '模型未能加载，请检查网络后重试。效果图仍可查看。',
          );
      },
    );
    return () => {
      alive = false;
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
