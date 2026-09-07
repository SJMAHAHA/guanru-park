import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {
  title: 'Guanru Park 3.0 · 建筑漫游',
  description:
    '现代别墅三维展示，精细材质与家具，可分层展开、剖切、切换昼夜与探索室内空间。',
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
