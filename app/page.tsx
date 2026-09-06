'use client';
import Image from 'next/image';
import { useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import {
  RotateCcw,
  Plus,
  Minus,
  MoveUpRight,
  PanelsTopLeft,
  Grid2X2,
  Box,
} from 'lucide-react';
import Viewer, { type View } from './viewer';
const floors = [
  { id: 'all', name: '完整建筑', note: '双翼体量、弧形基座与层层退台。' },
  {
    id: 'B1',
    name: 'B1',
    note: '康体娱乐、泳池与车库。单独显示本层，顶棚已隐藏。',
  },
  {
    id: '1F',
    name: '1F',
    note: '公共起居、餐厨与户外平台。单独显示本层，顶棚已隐藏。',
  },
  {
    id: '2F',
    name: '2F',
    note: '卧室套房、主卧露台与泳池。单独显示本层，顶棚已隐藏。',
  },
];
const views: { id: View; name: string; icon: typeof Box }[] = [
  { id: 'aerial', name: '鸟瞰', icon: Box },
  { id: 'east', name: '东侧', icon: PanelsTopLeft },
  { id: 'courtyard', name: '中庭', icon: MoveUpRight },
  { id: 'plan', name: '俯视', icon: Grid2X2 },
];
export default function Home() {
  const [floor, setFloor] = useState('all'),
    [view, setView] = useState<View>('aerial'),
    [furniture, setFurniture] = useState(true),
    [rotate, setRotate] = useState(false),
    [reset, setReset] = useState(0),
    [ready, setReady] = useState(false),
    [progress, setProgress] = useState(0),
    [error, setError] = useState(''),
    [attempt, setAttempt] = useState(0);
  const selected = floors.find((f) => f.id === floor)!;
  const zoom = (delta: number) => {
    document
      .querySelector('canvas')
      ?.dispatchEvent(
        new WheelEvent('wheel', {
          deltaY: delta,
          bubbles: true,
          cancelable: true,
        }),
      );
  };
  const retry = () => {
    setError('');
    setReady(false);
    setProgress(0);
    setAttempt((v) => v + 1);
  };
  return (
    <main className="workspace">
      <aside className="control-panel">
        <div className="brand-block">
          <div className="eyebrow">ARCHITECTURE / 01</div>
          <h1 className="brand">
            GUANRU
            <br />
            PARK
          </h1>
          <p className="project-label">现代别墅 · 建筑漫游</p>
        </div>
        <div>
          <span className="section-label">楼层</span>
          <Tabs value={floor} onValueChange={(v) => setFloor(String(v))}>
            <TabsList className="floor-tabs" aria-label="选择楼层">
              {floors.map((f) => (
                <TabsTrigger key={f.id} value={f.id}>
                  {f.name}
                </TabsTrigger>
              ))}
            </TabsList>
            {floors.map((f) => (
              <TabsContent key={f.id} value={f.id} className="floor-note">
                {f.note}
              </TabsContent>
            ))}
          </Tabs>
        </div>
        <div>
          <span className="section-label">视角</span>
          <div className="presets">
            {views.map((v) => (
              <button
                key={v.id}
                className="preset"
                aria-pressed={view === v.id}
                onClick={() => setView(v.id)}
              >
                <v.icon size={16} />
                {v.name}
              </button>
            ))}
          </div>
        </div>
        <div className="options">
          <span className="section-label">显示</span>
          <label className="switch-row" htmlFor="furniture">
            家具
            <Switch
              id="furniture"
              checked={furniture}
              onCheckedChange={setFurniture}
            />
          </label>
          <label className="switch-row" htmlFor="rotate">
            自动旋转
            <Switch
              id="rotate"
              checked={rotate}
              onCheckedChange={setRotate}
              disabled={view === 'plan'}
            />
          </label>
        </div>
        <p className="panel-foot">
          <span className="status-mark" />
          {ready ? '实时三维' : '建筑展示模型'}
          <br />
          根据参考图重建 · 层高约 3.15 m<br />
          材质为展示补充设计
        </p>
      </aside>
      <section className="stage" aria-label="建筑三维展示">
        <Viewer
          key={attempt}
          options={{ floor, view, furniture, rotate, reset }}
          onProgress={setProgress}
          onReady={() => {
            setReady(true);
            setProgress(100);
          }}
          onError={setError}
        />
        {(!ready || error) && (
          <Image
            unoptimized
            fill
            priority
            className="poster"
            src="/preview.jpg"
            alt="Guanru Park 别墅鸟瞰效果图"
          />
        )}
        <div className="stage-title">
          <strong>
            {selected.name}
            {view === 'plan' ? ' · 俯视' : ''}
          </strong>
          <span>GUANRU PARK / 3D</span>
        </div>
        <div className="stage-tools">
          <button
            className="icon-button"
            title="放大"
            aria-label="放大"
            onClick={() => zoom(-150)}
            disabled={!ready || !!error}
          >
            <Plus size={18} />
          </button>
          <button
            className="icon-button"
            title="缩小"
            aria-label="缩小"
            onClick={() => zoom(150)}
            disabled={!ready || !!error}
          >
            <Minus size={18} />
          </button>
          <button
            className="icon-button"
            title="重置当前视角"
            aria-label="重置当前视角"
            onClick={() => setReset((v) => v + 1)}
            disabled={!ready || !!error}
          >
            <RotateCcw size={17} />
          </button>
        </div>
        {error ? (
          <div className="load-box error-message" role="alert">
            <p>{error}</p>
            <button onClick={retry} className="retry-button">
              重新加载
            </button>
            <a href="/preview.jpg" target="_blank" rel="noreferrer">
              查看效果图
            </a>
          </div>
        ) : !ready ? (
          <output className="load-box" aria-live="polite">
            <p>
              {progress === 99
                ? '正在准备模型…'
                : `正在载入建筑${progress > 0 ? ` · ${progress}%` : '…'}`}
            </p>
            <Progress value={progress} aria-label="模型加载进度" />
          </output>
        ) : null}
        <div className="view-hint">
          <span className="desktop-hint">
            {view === 'plan'
              ? '右键平移 · 滚轮缩放'
              : '拖动旋转 · 滚轮缩放 · 右键平移'}
          </span>
          <span className="mobile-hint">
            {view === 'plan' ? '双指缩放与平移' : '单指旋转 · 双指缩放与平移'}
          </span>
        </div>
      </section>
    </main>
  );
}
