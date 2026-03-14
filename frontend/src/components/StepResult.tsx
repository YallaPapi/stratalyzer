'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import LoadingStep from './LoadingStep';

/* ─── Types ─── */

type StepStatus = 'idle' | 'loading' | 'complete' | 'error';

interface StepResultProps {
  stepNumber: number;
  stepName: string;
  subtitle: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any;
  status: StepStatus;
  error?: string;
}

const STEP_NAMES: Record<number, string> = {
  1: 'Creator Vision',
  2: 'Become the Niche',
  3: 'Unique Positioning',
  4: 'Lego Method',
  5: 'Monetization',
  6: 'Convert Hooks',
};

function formatLabel(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function isRecord(value: any): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function renderInlineValue(value: any): string {
  if (value == null) return '';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === 'string' || typeof item === 'number' || typeof item === 'boolean') {
          return String(item);
        }
        if (isRecord(item)) {
          return String(item.title || item.name || item.text || JSON.stringify(item));
        }
        return JSON.stringify(item);
      })
      .join(', ');
  }

  if (isRecord(value)) {
    return String(value.title || value.name || value.text || JSON.stringify(value));
  }

  return String(value);
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ReadableValue({ value }: { value: any }) {
  if (value == null || value === '') return null;

  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return <p className="text-sm leading-relaxed text-white">{String(value)}</p>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return null;

    const allScalar = value.every(
      (item) =>
        item == null ||
        typeof item === 'string' ||
        typeof item === 'number' ||
        typeof item === 'boolean'
    );

    if (allScalar) {
      return (
        <div className="flex flex-wrap gap-2">
          {value.map((item, i) => (
            <span
              key={i}
              className="rounded-lg px-3 py-1.5 text-xs font-medium text-white"
              style={{ backgroundColor: 'rgba(109, 90, 205, 0.12)', border: '1px solid rgba(109, 90, 205, 0.2)' }}
            >
              {String(item)}
            </span>
          ))}
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {value.map((item, i) => (
          <div
            key={i}
            className="rounded-xl border p-4"
            style={{ backgroundColor: '#111113', borderColor: '#27272a' }}
          >
            <ReadableValue value={item} />
          </div>
        ))}
      </div>
    );
  }

  if (isRecord(value)) {
    return (
      <div className="space-y-3">
        {Object.entries(value).map(([key, nested]) => (
          <div key={key}>
            <h5 className="mb-1 text-xs font-semibold uppercase tracking-wider" style={{ color: '#71717a' }}>
              {formatLabel(key)}
            </h5>
            <ReadableValue value={nested} />
          </div>
        ))}
      </div>
    );
  }

  return <p className="text-sm leading-relaxed text-white">{String(value)}</p>;
}

/* ─── Sub-renderers ─── */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function RenderStep1({ data }: { data: any }) {
  const coreMessage = data?.core_message || data?.coreMessage;
  const pillars = data?.content_pillars || data?.contentPillars || [];
  const avatar = data?.avatar || data?.creator_avatar;
  const truth = data?.your_truth || data?.yourTruth;
  const weeklyBalance = data?.weekly_balance || data?.weeklyBalance;

  return (
    <div className="space-y-5">
      {coreMessage && (
        <blockquote
          className="rounded-xl border-l-4 py-3 pl-5 pr-4 text-base font-medium italic text-white"
          style={{ borderColor: '#6d5acd', backgroundColor: 'rgba(109, 90, 205, 0.06)' }}
        >
          &ldquo;{coreMessage}&rdquo;
        </blockquote>
      )}

      {pillars.length > 0 && (
        <div>
          <h4 className="mb-3 text-sm font-semibold uppercase tracking-wider" style={{ color: '#a1a1aa' }}>
            Content Pillars
          </h4>
          <div className="grid gap-3 sm:grid-cols-2">
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {pillars.map((pillar: any, i: number) => (
              <div
                key={i}
                className="rounded-xl border p-4 transition-colors duration-200"
                style={{ backgroundColor: '#111113', borderColor: '#27272a' }}
              >
                <div className="mb-1 flex items-center gap-2">
                  <span className="font-display text-sm font-semibold text-white">
                    {pillar.name || pillar.title || `Pillar ${i + 1}`}
                  </span>
                  {(pillar.is_anchor || pillar.anchor) && (
                    <span
                      className="rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase"
                      style={{ backgroundColor: 'rgba(109, 90, 205, 0.15)', color: '#8b7ae0' }}
                    >
                      Anchor
                    </span>
                  )}
                </div>
                <p className="text-xs leading-relaxed" style={{ color: '#a1a1aa' }}>
                  {pillar.description || pillar.desc || ''}
                </p>
                {pillar.anchor_rationale && (
                  <p className="mt-2 text-xs italic" style={{ color: '#8b7ae0' }}>
                    {pillar.anchor_rationale}
                  </p>
                )}
                {Array.isArray(pillar.example_content_ideas) && pillar.example_content_ideas.length > 0 && (
                  <div className="mt-3 space-y-1">
                    {pillar.example_content_ideas.map((idea: string, ideaIndex: number) => (
                      <p key={ideaIndex} className="text-xs leading-relaxed text-white">
                        {idea}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {avatar && (
        <div className="rounded-xl border p-4" style={{ backgroundColor: '#111113', borderColor: '#27272a' }}>
          <h4 className="mb-2 text-sm font-semibold" style={{ color: '#a1a1aa' }}>
            Creator Avatar
          </h4>
          <ReadableValue value={avatar} />
        </div>
      )}

      {truth && (
        <div className="rounded-xl border p-4" style={{ backgroundColor: '#111113', borderColor: '#27272a' }}>
          <h4 className="mb-2 text-sm font-semibold" style={{ color: '#a1a1aa' }}>
            Your Truth
          </h4>
          <ReadableValue value={truth} />
        </div>
      )}

      {weeklyBalance && (
        <div className="rounded-xl border p-4" style={{ backgroundColor: '#111113', borderColor: '#27272a' }}>
          <h4 className="mb-2 text-sm font-semibold" style={{ color: '#a1a1aa' }}>
            Weekly Balance
          </h4>
          <ReadableValue value={weeklyBalance} />
        </div>
      )}

      <FallbackFields
        data={data}
        exclude={[
          'core_message',
          'coreMessage',
          'content_pillars',
          'contentPillars',
          'avatar',
          'creator_avatar',
          'your_truth',
          'yourTruth',
          'weekly_balance',
          'weeklyBalance',
        ]}
      />
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function RenderStep2({ data }: { data: any }) {
  const tagline = data?.branded_message?.tagline || data?.tagline || data?.niche_tagline;
  const brandedMessage = data?.branded_message;
  const blueprint = data?.blueprint || data?.niche_blueprint;
  const blueprintPillars = blueprint?.content_pillars || [];
  const visualIdentity = blueprint?.visual_identity;
  const operationalTemplate = blueprint?.operational_template;
  const zeroDollarToolkit = blueprint?.zero_dollar_toolkit || [];

  return (
    <div className="space-y-5">
      {tagline && (
        <div className="text-center">
          <p
            className="inline-block rounded-xl px-6 py-3 font-display text-xl font-bold tracking-tight text-white"
            style={{ background: 'linear-gradient(135deg, rgba(109, 90, 205, 0.12) 0%, rgba(79, 143, 255, 0.12) 100%)' }}
          >
            {tagline}
          </p>
        </div>
      )}

      {brandedMessage && (
        <div className="rounded-xl border p-5" style={{ backgroundColor: '#111113', borderColor: '#27272a' }}>
          <h4 className="mb-3 text-sm font-semibold uppercase tracking-wider" style={{ color: '#a1a1aa' }}>
            Branded Message
          </h4>
          <ReadableValue value={Object.fromEntries(Object.entries(brandedMessage).filter(([key]) => key !== 'tagline'))} />
        </div>
      )}

      {blueprint && (
        <div className="rounded-xl border p-5" style={{ backgroundColor: '#111113', borderColor: '#27272a' }}>
          <h4 className="mb-3 text-sm font-semibold uppercase tracking-wider" style={{ color: '#a1a1aa' }}>
            Blueprint
          </h4>
          {blueprint.niche_you_become && (
            <div className="mb-4 rounded-xl border p-4" style={{ backgroundColor: '#18181b', borderColor: '#27272a' }}>
              <h5 className="mb-1 text-xs font-semibold uppercase tracking-wider" style={{ color: '#71717a' }}>
                Niche You Become
              </h5>
              <p className="text-sm leading-relaxed text-white">{blueprint.niche_you_become}</p>
            </div>
          )}

          {Array.isArray(blueprintPillars) && blueprintPillars.length > 0 && (
            <div className="mb-4">
              <h5 className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: '#71717a' }}>
                Content Pillars
              </h5>
              <div className="grid gap-3">
                {blueprintPillars.map((pillar: any, index: number) => (
                  <div
                    key={index}
                    className="rounded-xl border p-4"
                    style={{ backgroundColor: '#18181b', borderColor: '#27272a' }}
                  >
                    <p className="font-display text-sm font-semibold text-white">
                      {pillar.pillar || pillar.name || `Pillar ${index + 1}`}
                    </p>
                    {pillar.description && (
                      <p className="mt-1 text-sm leading-relaxed" style={{ color: '#a1a1aa' }}>
                        {pillar.description}
                      </p>
                    )}
                    {pillar.example_post && (
                      <p className="mt-2 text-xs leading-relaxed" style={{ color: '#8b7ae0' }}>
                        {pillar.example_post}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {visualIdentity && (
            <div className="mb-4 rounded-xl border p-4" style={{ backgroundColor: '#18181b', borderColor: '#27272a' }}>
              <h5 className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: '#71717a' }}>
                Visual Identity
              </h5>
              <ReadableValue value={visualIdentity} />
            </div>
          )}

          {operationalTemplate && (
            <div className="mb-4 rounded-xl border p-4" style={{ backgroundColor: '#18181b', borderColor: '#27272a' }}>
              <h5 className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: '#71717a' }}>
                Operational Template
              </h5>
              <ReadableValue value={operationalTemplate} />
            </div>
          )}

          {Array.isArray(zeroDollarToolkit) && zeroDollarToolkit.length > 0 && (
            <div className="mb-4">
              <h5 className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: '#71717a' }}>
                Zero-Dollar Toolkit
              </h5>
              <div className="grid gap-3 sm:grid-cols-2">
                {zeroDollarToolkit.map((tool: any, index: number) => (
                  <div
                    key={index}
                    className="rounded-xl border p-4"
                    style={{ backgroundColor: '#18181b', borderColor: '#27272a' }}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-display text-sm font-semibold text-white">{tool.tool || `Tool ${index + 1}`}</p>
                      {tool.cost && (
                        <span className="text-xs font-semibold" style={{ color: '#8b7ae0' }}>
                          {tool.cost}
                        </span>
                      )}
                    </div>
                    {tool.use_case && (
                      <p className="mt-2 text-sm leading-relaxed" style={{ color: '#a1a1aa' }}>
                        {tool.use_case}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <FallbackFields
            data={blueprint}
            exclude={[
              'niche_you_become',
              'content_pillars',
              'visual_identity',
              'operational_template',
              'zero_dollar_toolkit',
            ]}
          />
        </div>
      )}
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function RenderStep3({ data }: { data: any }) {
  // API returns a plain array of positioned content items
  const items = Array.isArray(data)
    ? data
    : data?.positioned_versions || data?.positionedVersions || data?.versions || [];

  const normalizedItems = Array.isArray(items)
    ? items.flatMap((item) => {
        if (typeof item === 'string') {
          return [{ positioned_version: item }];
        }

        if (Array.isArray(item?.versions)) {
          return item.versions.map((version: any) => ({
            generic_version: item.original || version.generic_version || version.genericVersion,
            positioned_version: version.positioned_version || version.positionedVersion || version.text || version.title,
            why_this_wins: version.why_this_wins || version.whyThisWins,
            opening_script: version.opening_script || version.openingScript,
          }));
        }

        return [item];
      })
    : [];

  if (normalizedItems.length > 0) {
    return (
      <div className="space-y-4">
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        {normalizedItems.map((item: any, i: number) => (
          <div
            key={i}
            className="rounded-xl border p-4"
            style={{ backgroundColor: '#111113', borderColor: '#27272a' }}
          >
            {(item.generic_version || item.genericVersion) && (
              <p className="mb-2 text-xs font-medium" style={{ color: '#71717a' }}>
                Generic: {item.generic_version || item.genericVersion}
              </p>
            )}
            <div className="space-y-3">
              <p className="font-display text-sm font-semibold text-white">
                {item.positioned_version || item.positionedVersion || item.text || item.title}
              </p>
              {(item.why_this_wins || item.whyThisWins) && (
                <p className="text-sm leading-relaxed" style={{ color: '#a1a1aa' }}>
                  {item.why_this_wins || item.whyThisWins}
                </p>
              )}
              {(item.opening_script || item.openingScript) && (
                <div className="rounded-lg border p-3" style={{ backgroundColor: '#18181b', borderColor: '#27272a' }}>
                  <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider" style={{ color: '#71717a' }}>
                    Opening Script
                  </p>
                  <p className="text-sm leading-relaxed text-white">
                    {item.opening_script || item.openingScript}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return <FallbackFields data={data} exclude={[]} />;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function RenderStep4({ data }: { data: any }) {
  const hooks = data?.hooks || [];
  // distill is a dict: { struggles: [...], topics: [...], desires: [...] }
  const distill = data?.distill || data?.distill_results;

  return (
    <div className="space-y-5">
      {distill && typeof distill === 'object' && !Array.isArray(distill) && (
        <div className="space-y-4">
          {Object.entries(distill).map(([category, items]) => (
            <div key={category}>
              <h4 className="mb-3 text-sm font-semibold uppercase tracking-wider" style={{ color: '#a1a1aa' }}>
                {category.replace(/_/g, ' ')}
              </h4>
              <div className="flex flex-wrap gap-2">
                {Array.isArray(items) && items.map((item: string, i: number) => (
                  <span
                    key={i}
                    className="rounded-lg px-3 py-1.5 text-xs font-medium text-white"
                    style={{ backgroundColor: 'rgba(109, 90, 205, 0.12)', border: '1px solid rgba(109, 90, 205, 0.2)' }}
                  >
                    {renderInlineValue(item)}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {Array.isArray(hooks) && hooks.length > 0 && (
        <div>
          <h4 className="mb-3 text-sm font-semibold uppercase tracking-wider" style={{ color: '#a1a1aa' }}>
            Hooks ({hooks.length})
          </h4>
          <div className="space-y-0 overflow-hidden rounded-xl border" style={{ borderColor: '#27272a' }}>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {hooks.map((hook: any, i: number) => (
              <div
                key={i}
                className="flex items-start gap-3 border-b px-4 py-3 last:border-b-0"
                style={{
                  backgroundColor: i % 2 === 0 ? '#111113' : '#18181b',
                  borderColor: '#27272a',
                }}
              >
                <span
                  className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded text-[10px] font-bold text-white"
                  style={{ backgroundColor: 'rgba(109, 90, 205, 0.2)', color: '#8b7ae0' }}
                >
                  {i + 1}
                </span>
                <p className="text-sm text-white">
                  {typeof hook === 'string' ? hook : hook.text || hook.hook || renderInlineValue(hook)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function RenderStep5({ data }: { data: any }) {
  // API returns { "DOSER": { ... }, "Layered Offers": { ... } } — framework names are top-level keys
  const frameworks = Array.isArray(data?.frameworks || data?.monetization || data?.products)
    ? (data.frameworks || data.monetization || data.products)
    : (data && typeof data === 'object' && !Array.isArray(data))
      ? Object.entries(data).map(([name, value]) => ({ name, ...(typeof value === 'object' && value !== null ? value as Record<string, unknown> : { details: value }) }))
      : [];
  const [expanded, setExpanded] = useState<number | null>(null);

  if (Array.isArray(frameworks) && frameworks.length > 0) {
    return (
      <div className="space-y-3">
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        {frameworks.map((fw: any, i: number) => {
          const isOpen = expanded === i;
          return (
            <div
              key={i}
              className="overflow-hidden rounded-xl border transition-colors duration-200"
              style={{ backgroundColor: '#111113', borderColor: isOpen ? 'rgba(109, 90, 205, 0.3)' : '#27272a' }}
            >
              <button
                onClick={() => setExpanded(isOpen ? null : i)}
                className="flex w-full items-center justify-between px-5 py-4 text-left"
              >
                <div>
                  <p className="font-display text-sm font-semibold text-white">
                    {fw.name || fw.product_name || fw.title || `Product ${i + 1}`}
                  </p>
                  {(fw.price || fw.price_point) && (
                    <span className="mt-1 inline-block text-xs font-medium" style={{ color: '#6d5acd' }}>
                      {fw.price || fw.price_point}
                    </span>
                  )}
                </div>
                {isOpen ? (
                  <ChevronUp size={16} style={{ color: '#71717a' }} />
                ) : (
                  <ChevronDown size={16} style={{ color: '#71717a' }} />
                )}
              </button>
              <AnimatePresence>
                {isOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="overflow-hidden"
                  >
                    <div className="border-t px-5 pb-4 pt-3" style={{ borderColor: '#27272a' }}>
                      <FallbackFields data={fw} exclude={['name', 'product_name', 'title', 'price', 'price_point']} />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    );
  }

  return <FallbackFields data={data} exclude={[]} />;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function RenderStep6({ data }: { data: any }) {
  // API returns a plain array of hook strings/objects
  const hooks = Array.isArray(data)
    ? data
    : data?.hooks || data?.converted_hooks || data?.conversion_hooks || [];

  if (Array.isArray(hooks) && hooks.length > 0) {
    return (
      <div className="space-y-2">
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        {hooks.map((hook: any, i: number) => {
          const text = typeof hook === 'string' ? hook : hook.text || hook.hook || '';
          const product = typeof hook === 'object' ? hook.product || hook.product_name || '' : '';

          return (
            <div
              key={i}
              className="flex items-start gap-3 rounded-xl border px-4 py-3"
              style={{ backgroundColor: '#111113', borderColor: '#27272a' }}
            >
              <span
                className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded text-[10px] font-bold"
                style={{ backgroundColor: 'rgba(109, 90, 205, 0.2)', color: '#8b7ae0' }}
              >
                {i + 1}
              </span>
              <div className="min-w-0">
                <p className="text-sm text-white">{text || renderInlineValue(hook)}</p>
                {product && (
                  <span className="mt-1 inline-block text-xs font-medium" style={{ color: '#6d5acd' }}>
                    {product}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return <FallbackFields data={data} exclude={[]} />;
}

/* ─── Fallback: render any keys not already handled ─── */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function FallbackFields({ data, exclude }: { data: any; exclude: string[] }) {
  if (!data || typeof data !== 'object') return null;
  const remaining = Object.entries(data).filter(([k]) => !exclude.includes(k));
  if (remaining.length === 0) return null;

  return (
    <div className="space-y-3">
      {remaining.map(([key, value]) => (
        <div key={key} className="rounded-xl border p-4" style={{ backgroundColor: '#111113', borderColor: '#27272a' }}>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color: '#71717a' }}>
            {formatLabel(key)}
          </h4>
          <ReadableValue value={value} />
        </div>
      ))}
    </div>
  );
}

/* ─── Main Component ─── */

const RENDERERS: Record<number, React.ComponentType<{ data: unknown }>> = {
  1: RenderStep1,
  2: RenderStep2,
  3: RenderStep3,
  4: RenderStep4,
  5: RenderStep5,
  6: RenderStep6,
};

export default function StepResult({
  stepNumber,
  stepName,
  subtitle,
  data,
  status,
  error,
}: StepResultProps) {
  if (status === 'idle') return null;

  if (status === 'loading') {
    return (
      <LoadingStep
        stepNumber={stepNumber}
        stepName={stepName || STEP_NAMES[stepNumber] || `Step ${stepNumber}`}
      />
    );
  }

  if (status === 'error') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="rounded-xl border p-6"
        style={{ backgroundColor: '#18181b', borderColor: 'rgba(239, 68, 68, 0.3)' }}
      >
        <div className="flex items-center gap-3">
          <AlertCircle size={20} className="shrink-0 text-red-400" />
          <div>
            <p className="text-sm font-medium text-white">
              Step {stepNumber} failed
            </p>
            <p className="mt-1 text-xs text-red-400">{error || 'An unknown error occurred'}</p>
          </div>
        </div>
      </motion.div>
    );
  }

  const Renderer = RENDERERS[stepNumber];

  return (
    <motion.div
      initial={{ opacity: 0, y: 24, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="overflow-hidden rounded-xl border"
      style={{ backgroundColor: '#18181b', borderColor: '#27272a' }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 border-b px-6 py-4" style={{ borderColor: '#27272a' }}>
        <span
          className="inline-flex items-center rounded-lg px-2.5 py-1 text-xs font-semibold text-white"
          style={{ background: 'linear-gradient(135deg, #6d5acd 0%, #4f8fff 100%)' }}
        >
          Step {stepNumber}
        </span>
        <div>
          <h3 className="font-display text-base font-semibold tracking-tight text-white">
            {stepName || STEP_NAMES[stepNumber]}
          </h3>
          {subtitle && (
            <p className="text-xs" style={{ color: '#71717a' }}>
              {subtitle}
            </p>
          )}
        </div>
        <span
          className="ml-auto flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase"
          style={{ backgroundColor: 'rgba(16, 185, 129, 0.12)', color: '#10b981' }}
        >
          <Check size={12} />
          Complete
        </span>
      </div>

      {/* Body */}
      <div className="p-6">
        {Renderer ? <Renderer data={data} /> : <FallbackFields data={data} exclude={[]} />}
      </div>
    </motion.div>
  );
}
