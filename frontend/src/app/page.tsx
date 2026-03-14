'use client';

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap } from 'lucide-react';
import Sidebar from '@/components/Sidebar';
import StepInput from '@/components/StepInput';
import StepResult from '@/components/StepResult';
import { runStep } from '@/lib/api';
import type { PipelineInputs } from '@/lib/api';

/* ─── Pipeline step definitions ─── */
const STEPS = [
  { key: 'step1', name: 'Creator Vision', subtitle: 'Core message, pillars & avatar' },
  { key: 'step2', name: 'Become the Niche', subtitle: 'Tagline & niche blueprint' },
  { key: 'step3', name: 'Unique Positioning', subtitle: 'Differentiated content angles' },
  { key: 'step4', name: 'Lego Method', subtitle: 'Hooks & distilled frameworks' },
  { key: 'step5', name: 'Monetization', subtitle: 'Product frameworks & pricing' },
  { key: 'step6', name: 'Convert Hooks', subtitle: 'Conversion-ready hooks' },
];

type StepStatus = 'idle' | 'loading' | 'complete' | 'error';

interface StepState {
  status: StepStatus;
  data: unknown;
  error?: string;
}

const initialInputs: PipelineInputs = {
  story: '',
  skills: '',
  audience: '',
  situation: '',
  product: '',
};

export default function Home() {
  const [inputs, setInputs] = useState<PipelineInputs>(initialInputs);
  const [currentStep, setCurrentStep] = useState(0);
  const [stepResults, setStepResults] = useState<StepState[]>(
    STEPS.map(() => ({ status: 'idle' as StepStatus, data: null }))
  );
  const [isRunning, setIsRunning] = useState(false);
  const [pipelineComplete, setPipelineComplete] = useState(false);

  const completedSteps = stepResults
    .map((s, i) => (s.status === 'complete' ? i + 1 : -1))
    .filter((n) => n > 0);

  const updateStep = useCallback((index: number, update: Partial<StepState>) => {
    setStepResults((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...update };
      return next;
    });
  }, []);

  const handleRun = useCallback(async () => {
    setIsRunning(true);
    setPipelineComplete(false);
    setStepResults(STEPS.map(() => ({ status: 'idle' as StepStatus, data: null })));

    const { story, skills, audience, situation, product } = inputs;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const results: Record<string, any> = {};

    for (let i = 0; i < STEPS.length; i++) {
      const step = STEPS[i];
      setCurrentStep(i + 1);
      updateStep(i, { status: 'loading' });

      try {
        let body: Record<string, unknown>;

        switch (step.key) {
          case 'step1':
            body = { story, skills, audience, situation, product };
            break;
          case 'step2':
            body = { story, skills, audience, situation, step1_result: results.step1 };
            break;
          case 'step3':
            body = { story, situation, step1_result: results.step1, step2_result: results.step2 };
            break;
          case 'step4':
            body = { story, skills, audience, situation, step1_result: results.step1, step2_result: results.step2 };
            break;
          case 'step5':
            body = { story, skills, audience, situation, product, step1_result: results.step1, step2_result: results.step2, frameworks: ['DOSER', 'Layered Offers'] };
            break;
          case 'step6':
            body = { step1_result: results.step1, step2_result: results.step2, step4_distill: results.step4?.distill, step5_results: results.step5 };
            break;
          default:
            body = {};
        }

        const result = await runStep(step.key, body);
        results[step.key] = result;
        updateStep(i, { status: 'complete', data: result });
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        updateStep(i, { status: 'error', error: message });
        break;
      }
    }

    setIsRunning(false);
    setPipelineComplete(true);
  }, [inputs, updateStep]);

  const hasResults = stepResults.some((s) => s.status !== 'idle');

  return (
    <div className="flex min-h-screen" style={{ backgroundColor: '#09090b' }}>
      <Sidebar currentStep={currentStep} completedSteps={completedSteps} />

      {/* Main content */}
      <main className="ml-[260px] flex-1">
        {/* Top bar */}
        <header
          className="sticky top-0 z-40 flex items-center justify-between border-b px-8 py-4"
          style={{
            backgroundColor: 'rgba(9, 9, 11, 0.8)',
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            borderColor: '#27272a',
          }}
        >
          <h1 className="font-display text-xl font-bold tracking-tight text-white">
            Content Strategy Pipeline
          </h1>
          <div
            className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium"
            style={{ backgroundColor: '#111113', color: '#71717a' }}
          >
            <Zap size={12} style={{ color: '#6d5acd' }} />
            Powered by Grok + Claude + GPT
          </div>
        </header>

        {/* Content */}
        <div className="mx-auto max-w-3xl px-8 py-10">
          <AnimatePresence mode="wait">
            {!hasResults ? (
              <motion.div
                key="input-form"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <StepInput
                  inputs={inputs}
                  onChange={setInputs}
                  onSubmit={handleRun}
                  isRunning={isRunning}
                />
              </motion.div>
            ) : (
              <motion.div
                key="results-view"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                {/* Collapsed input summary */}
                <StepInput
                  inputs={inputs}
                  onChange={setInputs}
                  onSubmit={handleRun}
                  isRunning={isRunning}
                  collapsed
                />

                {/* Step results */}
                <div className="space-y-6">
                  {STEPS.map((step, i) => (
                    <StepResult
                      key={step.key}
                      stepNumber={i + 1}
                      stepName={step.name}
                      subtitle={step.subtitle}
                      data={stepResults[i].data}
                      status={stepResults[i].status}
                      error={stepResults[i].error}
                    />
                  ))}
                </div>

                {/* Pipeline complete banner */}
                {pipelineComplete && completedSteps.length === 6 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.3 }}
                    className="mt-8 rounded-xl border p-6 text-center"
                    style={{
                      background: 'linear-gradient(135deg, rgba(109, 90, 205, 0.08) 0%, rgba(79, 143, 255, 0.08) 100%)',
                      borderColor: 'rgba(109, 90, 205, 0.2)',
                    }}
                  >
                    <h3 className="font-display text-lg font-bold text-white">
                      Pipeline Complete
                    </h3>
                    <p className="mt-1 text-sm" style={{ color: '#a1a1aa' }}>
                      All 6 steps have been generated. Your content strategy is ready.
                    </p>
                  </motion.div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
