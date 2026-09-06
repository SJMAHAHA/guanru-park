'use client';
import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export type View = 'aerial' | 'east' | 'courtyard' | 'plan';
export type Options = {
  floor: string;
  view: View;
  furniture: boolean;
  rotate: boolean;
  reset: number;
};
export default function Viewer({
  options,
  onProgress,
  onReady,
  onError,
}: {
  options: Options;
  onProgress: (n: number) => void;
  onReady: () => void;
  onError: (s: string) => void;
}) {
  const host = useRef<HTMLDivElement>(null);
  const apply = useRef<((o: Options) => void) | null>(null);
  const latest = useRef(options);
  useEffect(() => {
    latest.current = options;
  }, [options]);
  const callbacks = useRef({ onProgress, onReady, onError });
  useEffect(() => {
    callbacks.current = { onProgress, onReady, onError };
  }, [onProgress, onReady, onError]);
  useEffect(() => {
    const el = host.current;
    if (!el) return;
    let alive = true,
      frame = 0,
      dirty = true,
      model: THREE.Group | undefined,
      lastFloor = '',
      lastView = '',
      lastReset = -1;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#e9eef0');
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: false,
        powerPreference: 'high-performance',
      });
    } catch {
      callbacks.current.onError(
        '当前浏览器无法启动三维显示。请尝试更新浏览器或开启硬件加速。',
      );
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    renderer.setSize(el.clientWidth, el.clientHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.18;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.shadowMap.autoUpdate = false;
    el.appendChild(renderer.domElement);
    renderer.domElement.tabIndex = 0;
    renderer.domElement.setAttribute(
      'aria-label',
      '建筑三维模型。拖动旋转、滚轮缩放、右键平移；方向键平移。',
    );
    const perspective = new THREE.PerspectiveCamera(38, 1, 0.1, 600);
    const ortho = new THREE.OrthographicCamera(-35, 35, 35, -35, 0.1, 600);
    let camera: THREE.PerspectiveCamera | THREE.OrthographicCamera =
      perspective;
    const controls = new OrbitControls<
      THREE.PerspectiveCamera | THREE.OrthographicCamera
    >(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.09;
    controls.minDistance = 9;
    controls.maxDistance = 220;
    controls.minZoom = 0.45;
    controls.maxZoom = 8;
    controls.maxPolarAngle = Math.PI * 0.49;
    controls.autoRotateSpeed = 0.65;
    controls.listenToKeyEvents(renderer.domElement);
    controls.addEventListener('change', () => {
      dirty = true;
    });
    scene.add(new THREE.HemisphereLight(0xdcebf6, 0x9c9b8d, 2.1));
    const sun = new THREE.DirectionalLight(0xfff1dd, 3.2);
    sun.position.set(35, 65, -35);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, {
      left: -48,
      right: 48,
      top: 48,
      bottom: -48,
      near: 1,
      far: 160,
    });
    sun.shadow.normalBias = 0.055;
    sun.shadow.bias = -0.0003;
    scene.add(sun);
    const pmrem = new THREE.PMREMGenerator(renderer);
    const room = new RoomEnvironment();
    const env = pmrem.fromScene(room, 0.04);
    scene.environment = env.texture;
    scene.environmentIntensity = 0.3;
    room.dispose();
    pmrem.dispose();
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(300, 300),
      new THREE.MeshStandardMaterial({ color: 0xd9e1e1, roughness: 1 }),
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.42;
    ground.receiveShadow = true;
    scene.add(ground);
    const resize = () => {
      const w = el.clientWidth,
        h = el.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h);
      perspective.aspect = w / h;
      perspective.updateProjectionMatrix();
      const half = 32 * Math.max(1, h / w);
      ortho.left = (-half * w) / h;
      ortho.right = (half * w) / h;
      ortho.top = half;
      ortho.bottom = -half;
      ortho.updateProjectionMatrix();
      dirty = true;
    };
    const observer = new ResizeObserver(resize);
    observer.observe(el);
    const applyOptions = (o: Options) => {
      if (!alive) return;
      if (model) {
        model.traverse((node) => {
          const f = node.userData.floor,
            cat = node.userData.category;
          if (f) {
            node.visible =
              (o.floor === 'all' || f === o.floor) &&
              (o.furniture || cat !== 'Furniture') &&
              (o.floor === 'all' || cat !== 'Ceilings');
          }
        });
        renderer.shadowMap.needsUpdate = true;
      }
      ground.visible = o.floor === 'all';
      controls.autoRotate =
        o.rotate &&
        o.view !== 'plan' &&
        !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (
        o.floor !== lastFloor ||
        o.view !== lastView ||
        o.reset !== lastReset
      ) {
        const y =
          o.floor === 'B1'
            ? 1.2
            : o.floor === '1F'
              ? 4.4
              : o.floor === '2F'
                ? 7.5
                : 3.3;
        camera = o.view === 'plan' ? ortho : perspective;
        controls.object = camera;
        controls.enableRotate = o.view !== 'plan';
        camera.up.set(0, o.view === 'plan' ? 0 : 1, o.view === 'plan' ? -1 : 0);
        if (o.view === 'plan') {
          camera.position.set(0, 90, 0);
          ortho.zoom = 1;
          ortho.updateProjectionMatrix();
        } else {
          const p = {
            aerial: [70, 47, -85],
            east: [100, 28, -31],
            courtyard: [54, 36, 75],
          }[o.view];
          const scale = Math.max(1, 0.9 / (el.clientWidth / el.clientHeight));
          camera.position.set(p[0] * scale, p[1] * scale, p[2] * scale);
        }
        controls.target.set(0, y, 0);
        camera.lookAt(controls.target);
        controls.update();
        controls.saveState();
        lastFloor = o.floor;
        lastView = o.view;
        lastReset = o.reset;
      }
      dirty = true;
    };
    apply.current = applyOptions;
    resize();
    applyOptions(latest.current);
    const animate = () => {
      if (!alive) return;
      frame = requestAnimationFrame(animate);
      const changed = controls.update();
      if (dirty || changed) {
        renderer.render(scene, camera);
        dirty = false;
      }
    };
    animate();
    const lost = (e: Event) => {
      e.preventDefault();
      callbacks.current.onError('三维显示已暂停，请点击重新加载。');
    };
    renderer.domElement.addEventListener('webglcontextlost', lost);
    new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).load(
      '/villa.glb',
      (gltf) => {
        if (!alive) {
          gltf.scene.traverse((node) => {
            if (node instanceof THREE.Mesh) {
              node.geometry.dispose();
              const ms = Array.isArray(node.material)
                ? node.material
                : [node.material];
              ms.forEach((m) => m.dispose());
            }
          });
          return;
        }
        model = gltf.scene;
        model.traverse((node) => {
          if (node instanceof THREE.Mesh) {
            node.castShadow = true;
            node.receiveShadow = true;
            const ms = Array.isArray(node.material)
              ? node.material
              : [node.material];
            for (const m of ms) {
              if (m.name === 'Clear glazing') {
                m.transparent = true;
                m.opacity = 0.22;
                m.depthWrite = false;
                node.castShadow = false;
              }
              if (m.name === 'Water') node.castShadow = false;
            }
          }
        });
        scene.add(model);
        applyOptions(latest.current);
        renderer.render(scene, camera);
        callbacks.current.onReady();
      },
      (xhr) => {
        if (alive && xhr.total > 0)
          callbacks.current.onProgress(
            Math.min(99, Math.round((xhr.loaded / xhr.total) * 100)),
          );
      },
      () => {
        if (alive)
          callbacks.current.onError('模型加载失败，请检查网络后重试。');
      },
    );
    return () => {
      alive = false;
      apply.current = null;
      cancelAnimationFrame(frame);
      observer.disconnect();
      controls.dispose();
      renderer.domElement.removeEventListener('webglcontextlost', lost);
      const geometries = new Set<THREE.BufferGeometry>(),
        materials = new Set<THREE.Material>();
      scene.traverse((node) => {
        if (node instanceof THREE.Mesh) {
          geometries.add(node.geometry);
          (Array.isArray(node.material)
            ? node.material
            : [node.material]
          ).forEach((m) => materials.add(m));
        }
      });
      geometries.forEach((g) => g.dispose());
      materials.forEach((m) => m.dispose());
      env.dispose();
      sun.shadow.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);
  useEffect(() => {
    apply.current?.(options);
  }, [options]);
  return <div className="scene-host" ref={host} />;
}
