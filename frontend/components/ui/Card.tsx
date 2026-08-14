import { ReactNode } from "react";

export default function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-card border border-rule bg-white p-5 ${className}`}>{children}</div>;
}
