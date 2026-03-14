'use client';

import { motion } from 'framer-motion';

const STEP_MODELS: Record<number, string> = {
  1: 'Grok',
  2: 'Grok',
  3: 'Grok',
  4: 'Grok + Claude',
  5: 'GPT-5.3',
  6: 'GPT-5.3',
};

interface LoadingStepProps {
  stepNumber: number;
  stepName: string;
}

export default function LoadingStep({ stepNumber, stepName }: LoadingStepProps) {
  const model = STEP_MODELS[stepNumber] || 'AI';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="relative overflow-hidden rounded-xl border"
      style={{
        backgroundColor: 'rgba(24, 24, 27, 0.7)',
        borderColor: 'rgba(109, 90, 205, 0.25)',
        boxShadow: '0 0 30px rgba(109, 90, 205, 0.08), 0 0 60px rgba(109, 90, 205, 0.04)',
      }}
    >
      {/* Animated border glow */}
      <div
        className="pointer-events-none absolute inset-0 rounded-xl"
        style={{
          boxShadow: 'inset 0 0 0 1px rgba(109, 90, 205, 0.15)',
        }}
      />

      <div className="p-6">
        {/* Header */}
        <div className="mb-5 flex items-center gap-3">
          <span
            className="inline-flex items-center rounded-lg px-2.5 py-1 text-xs font-semibold text-white"
            style={{ background: 'linear-gradient(135deg, #6d5acd 0%, #4f8fff 100%)' }}
          >
            Step {stepNumber}
          </span>
          <h3 className="font-display text-lg font-semibold tracking-tight text-white">
            {stepName}
          </h3>
        </div>

        {/* Generating text with pulsing dot */}
        <div className="mb-5 flex items-center gap-2">
          <motion.span
            className="inline-block h-2 w-2 rounded-full"
            style={{ backgroundColor: '#6d5acd' }}
            animate={{ opacity: [1, 0.3, 1], scale: [1, 0.85, 1] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          />
          <span className="text-sm" style={{ color: '#a1a1aa' }}>
            Generating with {model}...
          </span>
        </div>

        {/* Skeleton lines */}
        <div className="space-y-3">
          {[100, 85, 92, 60].map((width, i) => (
            <div key={i} className="relative h-3 overflow-hidden rounded" style={{ width: `${width}%`, backgroundColor: '#27272a' }}>
              <motion.div
                className="absolute inset-0"
                style={{
                  background:
                    'linear-gradient(90deg, transparent 0%, rgba(109, 90, 205, 0.08) 50%, transparent 100%)',
                }}
                animate={{ x: ['-100%', '200%'] }}
                transition={{
                  duration: 1.8,
                  repeat: Infinity,
                  ease: 'easeInOut',
                  delay: i * 0.15,
                }}
              />
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
