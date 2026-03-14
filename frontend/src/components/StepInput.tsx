'use client';

import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import type { PipelineInputs } from '@/lib/api';

const fields: {
  key: keyof PipelineInputs;
  label: string;
  placeholder: string;
  helper: string;
  rows: number;
}[] = [
  {
    key: 'story',
    label: 'Your Story',
    placeholder: "Tell us your creator origin story. What led you here? What's your background?",
    helper: 'Your unique journey becomes your brand foundation',
    rows: 4,
  },
  {
    key: 'skills',
    label: 'Your Skills',
    placeholder: 'What are you exceptionally good at? List your core competencies, expertise, and talents.',
    helper: 'These become your content pillars and authority signals',
    rows: 3,
  },
  {
    key: 'audience',
    label: 'Target Audience',
    placeholder: 'Who do you want to reach? Describe their demographics, pain points, and aspirations.',
    helper: 'Specificity here drives better positioning downstream',
    rows: 3,
  },
  {
    key: 'situation',
    label: 'Current Situation',
    placeholder: 'Where are you now? Your follower count, revenue, content frequency, platforms.',
    helper: 'Honest context helps the AI calibrate recommendations',
    rows: 3,
  },
  {
    key: 'product',
    label: 'Product / Offer',
    placeholder: 'What do you sell or plan to sell? Courses, coaching, SaaS, physical products?',
    helper: 'The pipeline will build a monetization strategy around this',
    rows: 3,
  },
];

interface StepInputProps {
  inputs: PipelineInputs;
  onChange: (inputs: PipelineInputs) => void;
  onSubmit: () => void;
  isRunning: boolean;
  collapsed?: boolean;
}

const containerVariants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: 'easeOut' as const } },
};

export default function StepInput({
  inputs,
  onChange,
  onSubmit,
  isRunning,
  collapsed = false,
}: StepInputProps) {
  const handleChange = (key: keyof PipelineInputs, value: string) => {
    onChange({ ...inputs, [key]: value });
  };

  if (collapsed) {
    return (
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        className="mb-8 rounded-xl border px-5 py-4"
        style={{ backgroundColor: '#18181b', borderColor: '#27272a' }}
      >
        <div className="flex items-center gap-3">
          <div
            className="flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold text-white"
            style={{ background: 'linear-gradient(135deg, #6d5acd 0%, #4f8fff 100%)' }}
          >
            <Sparkles size={14} />
          </div>
          <div>
            <span className="text-sm font-medium text-white">Pipeline inputs configured</span>
            <span className="ml-2 text-xs" style={{ color: '#71717a' }}>
              {Object.values(inputs).filter(Boolean).length}/5 fields filled
            </span>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="mx-auto w-full max-w-2xl"
    >
      <motion.div variants={itemVariants} className="mb-8 text-center">
        <h2 className="font-display text-3xl font-bold tracking-tight text-white">
          Configure Your Pipeline
        </h2>
        <p className="mt-2 text-sm" style={{ color: '#a1a1aa' }}>
          Feed the AI your creator context. Better inputs = better strategy.
        </p>
      </motion.div>

      <div className="space-y-5">
        {fields.map((field) => (
          <motion.div key={field.key} variants={itemVariants}>
            <label className="mb-1.5 block text-sm font-medium text-white">
              {field.label}
            </label>
            <textarea
              rows={field.rows}
              value={inputs[field.key]}
              onChange={(e) => handleChange(field.key, e.target.value)}
              placeholder={field.placeholder}
              disabled={isRunning}
              className="w-full resize-none rounded-xl border px-4 py-3 text-sm text-white placeholder-zinc-500 transition-all duration-200 focus:outline-none disabled:opacity-50"
              style={{
                backgroundColor: '#18181b',
                borderColor: '#27272a',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = '#6d5acd';
                e.currentTarget.style.boxShadow = '0 0 0 3px rgba(109, 90, 205, 0.15), 0 0 20px rgba(109, 90, 205, 0.1)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = '#27272a';
                e.currentTarget.style.boxShadow = 'none';
              }}
            />
            <p className="mt-1 text-xs" style={{ color: '#71717a' }}>
              {field.helper}
            </p>
          </motion.div>
        ))}
      </div>

      <motion.div variants={itemVariants} className="mt-8">
        <button
          onClick={onSubmit}
          disabled={isRunning}
          className="group relative flex w-full items-center justify-center gap-2 rounded-xl px-6 py-3.5 text-sm font-semibold text-white transition-all duration-200 hover:-translate-y-0.5 disabled:pointer-events-none disabled:opacity-50"
          style={{
            background: 'linear-gradient(135deg, #6d5acd 0%, #4f8fff 100%)',
            boxShadow: '0 0 20px rgba(109, 90, 205, 0.3), 0 4px 12px rgba(0, 0, 0, 0.3)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow =
              '0 0 30px rgba(109, 90, 205, 0.5), 0 8px 24px rgba(0, 0, 0, 0.4)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow =
              '0 0 20px rgba(109, 90, 205, 0.3), 0 4px 12px rgba(0, 0, 0, 0.3)';
          }}
        >
          <Sparkles size={16} />
          Run Pipeline
        </button>

        <p className="mt-4 text-center text-xs" style={{ color: '#71717a' }}>
          Steps 1-4a: Grok &middot; Step 4b: Claude &middot; Steps 5-6: GPT-5.3
        </p>
      </motion.div>
    </motion.div>
  );
}
