'use client';
import Image from 'next/image';
import { useMemo, useRef, useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Progress } from '@/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  RotateCcw,
  Plus,
  Minus,
  Maximize2,
  Images,
  Sun,
  Moon,
  Layers3,
  ScanLine,
  Box,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Settings2,
} from 'lucide-react';
import Viewer, {
  type ViewerAPI,
  type LabelPosition,
  type PerformanceStats,
} from './viewer';
import {
  FLOOR_NAMES,
  INTERIORS,
  LEVELS,
  PRESETS,
  ROOMS,
  type Floor,
  type View,
  type Options,
} from './model-state';
const floors: Floor[] = ['all', 'B1', '1F', '2F', '3F'];
const notes: Record<Floor, string> = {
  all: '双翼体量、弧形基座与层层退台。',
  B1: '泳池、SPA、健身娱乐与车库。',
  '1F': '公共起居、餐厨与户外平台。',
  '2F': '卧室套房、衣帽间与私属露台。',
  '3F': '局部房间与开敞屋顶平台。',
};
const views: View[] = ['aerial', 'east', 'courtyard', 'plan'];
const viewLabels: Record<View, string> = {
  aerial: '鸟瞰',
  east: '东侧',
  courtyard: '中庭',
  plan: '俯视',
  pool: '泳池露台',
  living: '主客厅',
  master: '主卧',
  kitchen: '西厨',
  bath: '主卫',
  chinese: '中厨',
  dining: '餐厅',
  office: '办公室',
  pavilion: '屋顶起居',
};
const gallery = [
  { id: '01_Aerial', title: '整体鸟瞰' },
  { id: '02_East', title: '东侧外观' },
  { id: '03_Courtyard', title: '双翼中庭' },
  { id: '04_Pool', title: '泳池与露台' },
  { id: '08_Living', title: '主客厅' },
  { id: '09_Master', title: '主卧套房' },
  { id: '10_Kitchen', title: '西厨' },
  { id: '13_Bath', title: '主卫 · 悬挑台盆' },
  { id: '14_Kitchen_Detail', title: '西厨 · 内嵌设备' },
  { id: '15_Chinese_Kitchen', title: '中厨' },
  { id: '11_Twilight', title: '傍晚灯光' },
  { id: '05_B1_Axon', title: 'B1 · 剖切轴测' },
  { id: '06_1F_Axon', title: '1F · 剖切轴测' },
  { id: '07_2F_Axon', title: '2F · 剖切轴测' },
  { id: '12_3F_Axon', title: '3F · 屋顶空间' },
];
export default function Home() {
  const [floor, setFloor] = useState<Floor>('all'),
    [view, setView] = useState<View>('aerial'),
    [stats, setStats] = useState<PerformanceStats | null>(null),
    [quality, setQuality] = useState<'high' | 'standard'>('high'),
    [furniture, setFurniture] = useState(true),
    [rotate, setRotate] = useState(false),
    [reset, setReset] = useState(0),
    [explode, setExplode] = useState(false),
    [reveal, setReveal] = useState(false),
    [cut, setCut] = useState(false),
    [cutHeight, setCutHeight] = useState(13.2),
    [evening, setEvening] = useState(false),
    [labels, setLabels] = useState(true),
    [focus, setFocus] = useState<string | null>(null),
    [ready, setReady] = useState(false),
    [progress, setProgress] = useState(0),
    [error, setError] = useState(''),
    [attempt, setAttempt] = useState(0),
    [labelPositions, setLabelPositions] = useState<LabelPosition[]>([]),
    [galleryIndex, setGalleryIndex] = useState(0),
    [settings, setSettings] = useState(false),
    [notice, setNotice] = useState('');
  const viewerApi = useRef<ViewerAPI | null>(null),
    stage = useRef<HTMLElement | null>(null);
  const options: Options = useMemo(
    () => ({
      floor,
      view,
      furniture,
      quality,
      rotate,
      reset,
      explode,
      reveal,
      cut,
      cutHeight,
      evening,
      labels,
      focus,
    }),
    [
      floor,
      view,
      furniture,
      quality,
      rotate,
      reset,
      explode,
      reveal,
      cut,
      cutHeight,
      evening,
      labels,
      focus,
    ],
  );
  const chooseFloor = (value: Floor) => {
    setFloor(value);
    setFocus(null);
    setView('aerial');
    setExplode(false);
    setReveal(false);
    setCut(false);
    setCutHeight(value === 'all' ? 13.2 : LEVELS[value] + 2.85);
  };
  const chooseView = (value: View) => {
    setView(value);
    setFocus(null);
    setRotate(false);
    if (INTERIORS.has(value) || value === 'pool') {
      setFloor('all');
      setExplode(false);
      setReveal(false);
      setCut(false);
    }
    if (value === 'plan') setExplode(false);
  };
  const retry = () => {
    setError('');
    setReady(false);
    setProgress(0);
    setAttempt((v) => v + 1);
  };
  const toggleExplode = (checked: boolean) => {
    setExplode(checked);
    setFloor('all');
    setFocus(null);
    setView('aerial');
    setCut(false);
    setReveal(false);
  };
  const fullscreen = async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else if (stage.current?.requestFullscreen)
        await stage.current.requestFullscreen();
      else setNotice('此浏览器不支持全屏，可横屏浏览。');
    } catch {
      setNotice('暂时无法进入全屏，请尝试横屏浏览。');
    }
  };
  const title = focus
    ? ROOMS.find((r) => r.id === focus)?.name
    : INTERIORS.has(view) || view === 'pool'
      ? PRESETS[view as Exclude<View, 'plan'>].title
      : explode
        ? '分层展开'
        : FLOOR_NAMES[floor];
  return (
    <main className="app-v2">
      <header className="topbar">
        <div className="wordmark">
          GUANRU PARK<span className="version-tag">3.0</span>
        </div>
        <span className="topbar-context">建筑 · 材质 · 空间</span>
        <Dialog>
          <DialogTrigger className="gallery-open">
            <Images size={17} />
            效果图集
          </DialogTrigger>
          <DialogContent className="render-dialog">
            <DialogTitle>{gallery[galleryIndex].title}</DialogTitle>
            <DialogDescription>
              Guanru Park 3.0 · Blender 效果图
            </DialogDescription>
            <div className="gallery-image">
              <Image
                unoptimized
                fill
                sizes="90vw"
                src={`/gallery/${gallery[galleryIndex].id}.jpg`}
                alt={gallery[galleryIndex].title}
              />
            </div>
            <div className="gallery-navigation">
              <button
                onClick={() =>
                  setGalleryIndex(
                    (i) => (i + gallery.length - 1) % gallery.length,
                  )
                }
                aria-label="上一张效果图"
              >
                <ChevronLeft size={18} />
              </button>
              <span>
                {galleryIndex + 1} / {gallery.length}
              </span>
              <button
                onClick={() => setGalleryIndex((i) => (i + 1) % gallery.length)}
                aria-label="下一张效果图"
              >
                <ChevronRight size={18} />
              </button>
            </div>
            <div className="gallery-thumbnails">
              {gallery.map((g, i) => (
                <button
                  key={g.id}
                  aria-label={g.title}
                  aria-pressed={i === galleryIndex}
                  onClick={() => setGalleryIndex(i)}
                >
                  <Image
                    unoptimized
                    width={100}
                    height={70}
                    src={`/gallery/thumb-${g.id}.jpg`}
                    alt=""
                  />
                  <span>{g.title}</span>
                </button>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      </header>
      <div className="workspace-v2">
        <aside
          className={`control-panel-v2 ${settings ? 'settings-open' : ''}`}
        >
          <div className="panel-heading">
            <span className="eyebrow">EXPLORE THE ARCHITECTURE</span>
            <h1>建筑漫游</h1>
            <p>Guanru Park 现代别墅</p>
          </div>
          <section className="floor-section">
            <div className="section-heading">
              <Layers3 size={16} />
              <h2>楼层</h2>
            </div>
            <Tabs value={floor} onValueChange={(v) => chooseFloor(v as Floor)}>
              <TabsList className="floor-tabs-v2" aria-label="选择楼层">
                {floors.map((f) => (
                  <TabsTrigger value={f} key={f}>
                    {f === 'all' ? '整栋' : f}
                  </TabsTrigger>
                ))}
              </TabsList>
              {floors.map((f) => (
                <TabsContent value={f} key={f} className="floor-description">
                  {notes[f]}
                </TabsContent>
              ))}
            </Tabs>
          </section>
          <section className="view-section">
            <div className="section-heading">
              <Box size={16} />
              <h2>视角</h2>
            </div>
            <div className="view-grid">
              {views.map((v) => (
                <button
                  key={v}
                  aria-pressed={view === v && !focus}
                  onClick={() => chooseView(v)}
                >
                  {viewLabels[v]}
                </button>
              ))}
            </div>
          </section>
          <section className="spatial-section">
            <label className="switch-row" htmlFor="explode">
              <span>分层展开</span>
              <Switch
                id="explode"
                checked={explode}
                onCheckedChange={toggleExplode}
              />
            </label>
            <label className="switch-row" htmlFor="reveal">
              <span>揭开屋顶</span>
              <Switch
                id="reveal"
                checked={reveal}
                disabled={floor !== 'all' || explode || INTERIORS.has(view)}
                onCheckedChange={setReveal}
              />
            </label>
            <label className="switch-row" htmlFor="cut">
              <span>
                <ScanLine size={15} />
                水平剖切
              </span>
              <Switch
                id="cut"
                checked={cut}
                disabled={explode}
                onCheckedChange={setCut}
              />
            </label>
            {cut && !explode && (
              <div className="cut-controls">
                <div>
                  <span id="cut-label">剖切高度</span>
                  <output>{cutHeight.toFixed(2)} m</output>
                </div>
                <Slider
                  aria-labelledby="cut-label"
                  value={[cutHeight]}
                  onValueChange={(v) =>
                    setCutHeight(Array.isArray(v) ? v[0] : v)
                  }
                  min={-0.1}
                  max={13.2}
                  step={0.05}
                />
              </div>
            )}
          </section>
          <section className="quality-section">
            <div className="section-heading">
              <h2>画质</h2>
            </div>
            <Tabs
              value={quality}
              onValueChange={(v) => setQuality(v as 'high' | 'standard')}
            >
              <TabsList aria-label="画质选择">
                <TabsTrigger value="high">高画质</TabsTrigger>
                <TabsTrigger value="standard">标准画质</TabsTrigger>
              </TabsList>
            </Tabs>
          </section>
          <section className="lighting-section">
            <div className="section-heading">
              <Sun size={16} />
              <h2>光线</h2>
            </div>
            <fieldset className="light-choices" aria-label="光线时段">
              <button aria-pressed={!evening} onClick={() => setEvening(false)}>
                <Sun size={16} />
                日景
              </button>
              <button aria-pressed={evening} onClick={() => setEvening(true)}>
                <Moon size={16} />
                傍晚
              </button>
            </fieldset>
          </section>
          <button
            className="mobile-settings"
            aria-expanded={settings}
            onClick={() => setSettings((v) => !v)}
          >
            <Settings2 size={15} />
            显示设置
          </button>
          <section className="display-section">
            <label className="switch-row" htmlFor="furniture">
              <span>家具与软装</span>
              <Switch
                id="furniture"
                checked={furniture}
                onCheckedChange={setFurniture}
              />
            </label>
            <label className="switch-row" htmlFor="labels">
              <span>空间名称</span>
              <Switch
                id="labels"
                checked={labels}
                disabled={floor === 'all'}
                onCheckedChange={setLabels}
              />
            </label>
            <label className="switch-row" htmlFor="rotate">
              <span>自动旋转</span>
              <Switch
                id="rotate"
                checked={rotate}
                disabled={view === 'plan' || INTERIORS.has(view)}
                onCheckedChange={setRotate}
              />
            </label>
          </section>
          {stats && (
            <details className="performance-readout">
              <summary>实时表现</summary>
              <button
                className="performance-test"
                onClick={() => viewerApi.current?.benchmark()}
              >
                测量当前视角 · 5 秒
              </button>
              <output
                aria-label="实时性能"
                data-gpu={stats.gpu}
                data-browser={stats.browser}
                data-quality={stats.quality}
                data-fps={stats.fps.toFixed(1)}
                data-render-ms={stats.renderMs.toFixed(2)}
                data-load-seconds={stats.loadSeconds.toFixed(2)}
                data-triangles={stats.triangles}
                data-calls={stats.calls}
                data-viewport={stats.viewport}
              >
                加载 {stats.loadSeconds.toFixed(1)} s ·{' '}
                {stats.fps > 0 ? `${stats.fps.toFixed(0)} FPS` : '按需绘制'}
                <br />
                {stats.viewport}
                <br />
                <small>{stats.gpu}</small>
              </output>
            </details>
          )}
          <div className="panel-caption">
            <span className="status-mark" />
            米制模型 · 层高约 3.15 m<br />
            依据参考图重建，材质为展示补充设计。
          </div>
        </aside>
        <section
          ref={stage}
          className={`stage-v2 ${evening ? 'is-evening' : ''}`}
          aria-label="Guanru Park 3.0 三维展示"
        >
          <Viewer
            key={attempt}
            apiRef={viewerApi}
            options={options}
            onProgress={setProgress}
            onReady={() => {
              setReady(true);
              setProgress(100);
            }}
            onError={setError}
            onLabels={setLabelPositions}
            onStats={setStats}
          />
          {(!ready || error) && (
            <Image
              unoptimized
              fill
              priority
              className="poster"
              src="/preview-v3.jpg"
              alt="Guanru Park 3.0 鸟瞰效果图"
            />
          )}
          <div className="stage-caption">
            <span>
              {floor === 'all' ? 'GUANRU PARK' : floor} /{' '}
              {view === 'plan' ? 'PLAN' : '3D VIEW'}
            </span>
            <h2>{title}</h2>
            {floor !== 'all' && <p>单独显示本层 · 点击空间名称可近看</p>}
          </div>
          <div className="stage-tools">
            <button
              className="icon-button"
              aria-label="放大"
              title="放大"
              disabled={!ready || !!error}
              onClick={() => viewerApi.current?.zoom(0.8)}
            >
              <Plus size={18} />
            </button>
            <button
              className="icon-button"
              aria-label="缩小"
              title="缩小"
              disabled={!ready || !!error}
              onClick={() => viewerApi.current?.zoom(1.25)}
            >
              <Minus size={18} />
            </button>
            <button
              className="icon-button"
              aria-label="重置视角"
              title="重置视角"
              disabled={!ready || !!error}
              onClick={() => {
                setFocus(null);
                setReset((v) => v + 1);
              }}
            >
              <RotateCcw size={17} />
            </button>
            <button
              className="icon-button fullscreen-button"
              aria-label="切换全屏"
              title="全屏"
              onClick={() => void fullscreen()}
            >
              <Maximize2 size={17} />
            </button>
          </div>
          {ready && !error && (
            <div className="room-labels">
              {labelPositions.map((l) => (
                <button
                  key={l.id}
                  className="room-label"
                  style={{ left: l.x, top: l.y }}
                  onClick={() => {
                    setFocus(l.id);
                    setView('aerial');
                    setRotate(false);
                  }}
                >
                  <i />
                  {l.name}
                  <ArrowUpRight size={12} />
                </button>
              ))}
            </div>
          )}
          {error ? (
            <div className="load-box error-message" role="alert">
              <p>{error}</p>
              <button className="retry-button" onClick={retry}>
                重新加载
              </button>
              <a href="/preview-v3.jpg" target="_blank" rel="noreferrer">
                查看效果图
              </a>
            </div>
          ) : !ready ? (
            <output className="load-box" aria-live="polite">
              <span className="loading-edition">GUANRU PARK 3.0</span>
              <p>
                {progress === 99
                  ? '正在准备材质与光照…'
                  : `正在载入精细模型${progress > 0 ? ` · ${progress}%` : '…'}`}
              </p>
              <Progress value={progress} aria-label="模型加载进度" />
            </output>
          ) : null}
          <div className="stage-bottom">
            <div className="closeup-tray">
              <span>走近看看</span>
              {(
                [
                  'pool',
                  'living',
                  'master',
                  'kitchen',
                  'chinese',
                  'bath',
                  'dining',
                  'office',
                  'pavilion',
                ] as View[]
              ).map((v) => (
                <button
                  key={v}
                  aria-pressed={view === v && !focus}
                  onClick={() => chooseView(v)}
                >
                  {viewLabels[v]}
                  <ArrowUpRight size={13} />
                </button>
              ))}
            </div>
            <p className="interaction-hint">
              {notice || (
                <>
                  <span className="desktop-hint">
                    {view === 'plan'
                      ? '滚轮缩放 · 右键平移'
                      : '拖动旋转 · 滚轮缩放 · 右键平移'}
                  </span>
                  <span className="mobile-hint">
                    {view === 'plan'
                      ? '双指缩放与平移'
                      : '单指旋转 · 双指缩放与平移'}
                  </span>
                </>
              )}
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
