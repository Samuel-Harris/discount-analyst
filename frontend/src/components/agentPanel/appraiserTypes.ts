export interface IntrinsicValueDistribution {
  currency: string;
  current_share_price: number;
  expected_intrinsic_value: number;
  p10_intrinsic_value: number;
  p25_intrinsic_value: number;
  p50_intrinsic_value: number;
  p75_intrinsic_value: number;
  p90_intrinsic_value: number;
  distribution_method: string;
  distribution_reasoning: string;
}

export interface ValuationMethodResult {
  method: string;
  role: "primary" | "cross_check";
  value_per_share?: number | null;
  low_value_per_share?: number | null;
  high_value_per_share?: number | null;
  weight_pct?: number | null;
}

export interface AppraiserOutput {
  ticker: string;
  company_name: string;
  valuation_date: string;
  summary: string;
  valuation_distribution: IntrinsicValueDistribution;
  methods: ValuationMethodResult[];
  data_quality: "High" | "Medium" | "Low";
  distribution_method?: string;
  distribution_reasoning?: string;
}
