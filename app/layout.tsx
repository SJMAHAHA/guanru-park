import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {
  title: 'Guanru Park · 建筑漫游',
  description: '现代别墅三维展示，可旋转、缩放与分层查看建筑、家具和空间。',
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
