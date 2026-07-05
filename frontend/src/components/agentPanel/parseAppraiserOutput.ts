import type {
  AppraiserOutput,
  IntrinsicValueDistribution,
} from "./appraiserTypes";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isPositiveNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

function isDistribution(value: unknown): value is IntrinsicValueDistribution {
  if (!isRecord(value)) return false;
  return (
    typeof value.currency === "string" &&
    isPositiveNumber(value.current_share_price) &&
    isPositiveNumber(value.expected_intrinsic_value) &&
    isPositiveNumber(value.p10_intrinsic_value) &&
    isPositiveNumber(value.p25_intrinsic_value) &&
    isPositiveNumber(value.p50_intrinsic_value) &&
    isPositiveNumber(value.p75_intrinsic_value) &&
    isPositiveNumber(value.p90_intrinsic_value) &&
    typeof value.distribution_method === "string" &&
    typeof value.distribution_reasoning === "string"
  );
}

function isMethod(value: unknown): boolean {
  if (!isRecord(value)) return false;
  return (
    typeof value.method === "string" &&
    (value.role === "primary" || value.role === "cross_check")
  );
}

function isAppraiserOutput(value: unknown): value is AppraiserOutput {
  if (!isRecord(value)) return false;
  const methods = value.methods;
  return (
    typeof value.ticker === "string" &&
    typeof value.company_name === "string" &&
    typeof value.valuation_date === "string" &&
    typeof value.summary === "string" &&
    isDistribution(value.valuation_distribution) &&
    Array.isArray(methods) &&
    methods.length > 0 &&
    methods.every(isMethod) &&
    (value.data_quality === "High" ||
      value.data_quality === "Medium" ||
      value.data_quality === "Low")
  );
}

export function parseAppraiserOutput(raw: string): AppraiserOutput | null {
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!isAppraiserOutput(parsed)) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function marginOfSafetyPct(
  currentPrice: number,
  expectedIntrinsic: number,
): number {
  return ((expectedIntrinsic - currentPrice) / currentPrice) * 100;
}
