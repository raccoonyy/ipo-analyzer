export interface OHLCVData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface IPOCompany {
  id: number;
  company_name: string;
  code: string;
  listing_date: string;
  industry: string;
  theme: string;
  ipo_price_lower: number;
  ipo_price_upper: number;
  ipo_price_confirmed: number;
  shares_offered: number;
  institutional_demand_rate: number;
  subscription_competition_rate: number;
  lockup_ratio: number;
  predicted_day0_high: number;
  predicted_day0_close: number;
  predicted_day1_close: number;
  predicted_day0_high_return: number;
  predicted_day0_close_return: number;
  predicted_day1_close_return: number;
  actual_day0_high?: number;
  actual_day0_close?: number;
  actual_day1_close?: number;
  actual_day0_high_return?: number;
  actual_day0_close_return?: number;
  actual_day1_close_return?: number;
  error_day0_close?: number;
  error_pct_day0_close?: number;
  day0_ohlcv?: OHLCVData;
  day1_ohlcv?: OHLCVData;
}

export interface IPOMetadata {
  generated_at: string;
  model_version: string;
  total_ipos: number;
  date_range: {
    start: string;
    end: string;
  };
  features_used: string[];
  model_type: string;
}

export interface IPODataResponse {
  metadata: IPOMetadata;
  ipos: IPOCompany[];
}

export type IPOData = IPOCompany[];
