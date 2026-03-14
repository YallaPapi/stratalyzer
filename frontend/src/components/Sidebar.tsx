'use client';

import { motion } from 'framer-motion';
import {
  Compass,
  Lightbulb,
  PenTool,
  Film,
  TrendingUp,
  DollarSign,
} from 'lucide-react';

const navItems = [
  { label: 'Strategy', icon: Compass, step: 1 },
  { label: 'Ideation', icon: Lightbulb, step: 2 },
  { label: 'Script Writer', icon: PenTool, step: 3 },
  { label: 'Production', icon: Film, step: 4 },
  { label: 'Growth', icon: TrendingUp, step: 5 },
  { label: 'Monetization', icon: DollarSign, step: 6 },
];

interface SidebarProps {
  currentStep: number;
  completedSteps: number[];
}

export default function Sidebar({ currentStep, completedSteps }: SidebarProps) {
  const progressPercent = (completedSteps.length / 6) * 100;
  const activeStep = currentStep > 0 ? currentStep : 1;

  return (
    <aside
      className="fixed left-0 top-0 z-50 flex h-screen w-[260px] flex-col border-r"
      style={{
        backgroundColor: '#18181b',
        borderColor: '#27272a',
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 pt-6 pb-5">
        <div
          className="flex h-9 w-9 items-center justify-center rounded-lg text-sm font-bold text-white"
          style={{ background: 'linear-gradient(135deg, #6d5acd 0%, #4f8fff 100%)' }}
        >
          M
        </div>
        <span className="font-display text-lg font-semibold tracking-tight text-white">
          MethodApp
        </span>
      </div>

      {/* Creator section */}
      <div className="mx-4 mb-5 rounded-xl px-4 py-3" style={{ backgroundColor: '#111113' }}>
        <div className="flex items-center gap-3">
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white"
            style={{ background: 'linear-gradient(135deg, #6d5acd 0%, #e84393 100%)' }}
          >
            J
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-medium text-white">@junyuh</div>
            <div className="truncate text-xs" style={{ color: '#71717a' }}>
              Content Method
            </div>
          </div>
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-3">
        <div className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-widest" style={{ color: '#71717a' }}>
          Pipeline
        </div>
        <ul className="space-y-0.5">
          {navItems.map((item) => {
            const isActive = item.step === activeStep;
            const isComplete = completedSteps.includes(item.step);
            const Icon = item.icon;

            return (
              <li key={item.label}>
                <motion.button
                  whileHover={{ x: 2 }}
                  transition={{ duration: 0.15 }}
                  className="relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium transition-colors duration-200"
                  style={{
                    color: isActive ? '#fafafa' : isComplete ? '#a1a1aa' : '#71717a',
                    backgroundColor: isActive ? 'rgba(109, 90, 205, 0.12)' : 'transparent',
                    boxShadow: isActive
                      ? 'inset 0 0 0 1px rgba(109, 90, 205, 0.2), 0 0 20px rgba(109, 90, 205, 0.08)'
                      : 'none',
                  }}
                >
                  <Icon
                    size={18}
                    style={{
                      color: isActive ? '#8b7ae0' : isComplete ? '#6d5acd' : '#71717a',
                    }}
                  />
                  <span>{item.label}</span>
                  {isComplete && (
                    <span
                      className="ml-auto h-1.5 w-1.5 rounded-full"
                      style={{ backgroundColor: '#10b981' }}
                    />
                  )}
                </motion.button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Bottom progress */}
      <div className="border-t px-5 py-5" style={{ borderColor: '#27272a' }}>
        <div className="mb-2 flex items-center justify-between">
          <span className="text-xs font-medium" style={{ color: '#a1a1aa' }}>
            Progress
          </span>
          <span className="text-xs font-semibold" style={{ color: '#fafafa' }}>
            Step {completedSteps.length} of 6
          </span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full" style={{ backgroundColor: '#27272a' }}>
          <motion.div
            className="h-full rounded-full"
            style={{
              background: 'linear-gradient(90deg, #6d5acd 0%, #4f8fff 100%)',
            }}
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
      </div>
    </aside>
  );
}
