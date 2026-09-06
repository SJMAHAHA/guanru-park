import type { Object3D } from 'three';
export type Floor = 'all' | 'B1' | '1F' | '2F' | '3F';
export type View =
  | 'aerial'
  | 'east'
  | 'courtyard'
  | 'plan'
  | 'pool'
  | 'living'
  | 'master'
  | 'kitchen';
export type Options = {
  floor: Floor;
  view: View;
  furniture: boolean;
  rotate: boolean;
  reset: number;
  explode: boolean;
  reveal: boolean;
  cut: boolean;
  cutHeight: number;
  evening: boolean;
  labels: boolean;
  focus: string | null;
};
export const LEVELS: Record<string, number> = {
  B1: 0,
  '1F': 3.15,
  '2F': 6.3,
  '3F': 9.45,
  Roof: 12.6,
  Site: -0.4,
};
export const FLOOR_NAMES: Record<Floor, string> = {
  all: '完整建筑',
  B1: 'B1 · 康体与娱乐',
  '1F': '1F · 起居与会客',
  '2F': '2F · 卧室与露台',
  '3F': '3F · 屋顶空间',
};
export const INTERIORS = new Set<View>(['living', 'master', 'kitchen']);
export const PRESETS: Record<
  Exclude<View, 'plan'>,
  {
    position: [number, number, number];
    target: [number, number, number];
    title: string;
    floor?: Floor;
    fov?: number;
  }
> = {
  aerial: { position: [70, 47, -85], target: [0, 3.3, 0], title: '整体鸟瞰' },
  east: { position: [100, 28, -31], target: [0, 4, 0], title: '东侧立面' },
  courtyard: { position: [54, 36, 75], target: [0, 4, 3], title: '双翼中庭' },
  pool: {
    position: [21.173, 10.2, -22.507],
    target: [-4.053, 5.1, -10.4],
    title: '泳池与露台',
    floor: 'all',
    fov: 43,
  },
  living: {
    position: [2.133, 4.75, -2.347],
    target: [-2.293, 4.35, -7.84],
    title: '主客厅',
    floor: 'all',
    fov: 67,
  },
  master: {
    position: [-8.533, 7.87, -10.507],
    target: [-12.8, 7.22, -14.24],
    title: '主卧套房',
    floor: 'all',
    fov: 67,
  },
  kitchen: {
    position: [-12.213, 4.77, -4.16],
    target: [-15.573, 4.22, -7.36],
    title: '西厨与休闲餐厅',
    floor: 'all',
    fov: 65,
  },
};
export type Room = {
  id: string;
  floor: Exclude<Floor, 'all'>;
  name: string;
  position: [number, number, number];
};
const p = (x: number, y: number, z: number): [number, number, number] => [
  (x - 1068) / 18.75,
  z,
  (y - 622) / 18.75,
];
export const ROOMS: Room[] = [
  { id: 'spa', floor: 'B1', name: 'SPA', position: p(667, 220, 0) },
  {
    id: 'indoor-pool',
    floor: 'B1',
    name: '室内泳池',
    position: p(795, 330, 0),
  },
  { id: 'bowling', floor: 'B1', name: '保龄球', position: p(1140, 386, 0) },
  { id: 'gym', floor: 'B1', name: '健身房', position: p(941, 516, 0) },
  { id: 'cinema', floor: 'B1', name: '家庭影院', position: p(721, 805, 0) },
  { id: 'garage', floor: 'B1', name: '车库', position: p(980, 928, 0) },
  { id: 'family', floor: '1F', name: '家庭客厅', position: p(836, 384, 3.15) },
  { id: 'living', floor: '1F', name: '主客厅', position: p(1050, 513, 3.15) },
  { id: 'dining', floor: '1F', name: '餐厅', position: p(903, 534, 3.15) },
  { id: 'kitchen', floor: '1F', name: '西厨', position: p(775, 502, 3.15) },
  { id: 'office', floor: '1F', name: '办公室', position: p(978, 677, 3.15) },
  {
    id: 'terrace',
    floor: '1F',
    name: '户外客餐区',
    position: p(836, 270, 3.15),
  },
  { id: 'master', floor: '2F', name: '主卧', position: p(851, 390, 6.3) },
  {
    id: 'master-living',
    floor: '2F',
    name: '主卧起居室',
    position: p(884, 478, 6.3),
  },
  { id: 'dressing', floor: '2F', name: '衣帽间', position: p(867, 572, 6.3) },
  { id: 'master-bath', floor: '2F', name: '主卫', position: p(742, 613, 6.3) },
  { id: 'guest', floor: '2F', name: '次卧', position: p(1341, 659, 6.3) },
  { id: 'staff', floor: '2F', name: '员工住宿', position: p(876, 915, 6.3) },
  {
    id: 'pavilion',
    floor: '3F',
    name: '屋顶房间',
    position: p(1031, 664, 9.45),
  },
  {
    id: 'roof-terrace',
    floor: '3F',
    name: '屋顶平台',
    position: p(830, 820, 9.45),
  },
];
export function groupState(floor: string, category: string, o: Options) {
  const isAll = o.floor === 'all';
  const visible =
    (isAll || floor === o.floor) &&
    (o.furniture || category !== 'Furniture') &&
    (!isAll ? category !== 'Ceilings' : true) &&
    (!isAll ||
      !o.reveal ||
      o.explode ||
      (!['3F', 'Roof'].includes(floor) && category !== 'Ceilings'));
  const offset =
    isAll && o.explode && floor !== 'Site'
      ? ((LEVELS[floor] ?? 0) / 3.15) * 5.5
      : 0;
  return { visible, offset };
}
export function applyGroups(model: Object3D, o: Options) {
  model.traverse((n) => {
    const f = n.userData.floor,
      cat = n.userData.category;
    if (typeof f === 'string' && typeof cat === 'string') {
      n.userData.baseY ??= n.position.y;
      const s = groupState(f, cat, o);
      n.visible = s.visible;
      n.position.y = n.userData.baseY + s.offset;
    }
  });
  model.updateMatrixWorld(true);
}
