import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { IPOCompany } from "@/types/ipo";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { TrendingUp, TrendingDown } from "lucide-react";
import { StockChart } from "./StockChart";

interface PredictionResultProps {
  company: IPOCompany | null;
}

export function PredictionResult({ company }: PredictionResultProps) {
  if (!company) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>예측 결과</CardTitle>
          <CardDescription>예측을 보려면 위에서 기업을 선택하세요</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center min-h-[300px] text-muted-foreground">
          기업이 선택되지 않았습니다. 드롭다운에서 기업을 선택하세요.
        </CardContent>
      </Card>
    );
  }

  const {
    ipo_price_confirmed,
    company_name,
    predicted_day0_high,
    predicted_day0_close,
    predicted_day1_close,
    predicted_day0_high_return,
    predicted_day0_close_return,
    predicted_day1_close_return,
  } = company;

  const chartData = [
    { name: '공모가', value: ipo_price_confirmed },
    { name: '상장일 최고가', value: predicted_day0_high },
    { name: '상장일 종가', value: predicted_day0_close },
    { name: '다음날 종가', value: predicted_day1_close },
  ];

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>예측 결과</CardTitle>
        <CardDescription>
          {company_name}의 예측 가격
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Numeric Results */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 border rounded-lg bg-card">
            <p className="text-sm text-muted-foreground">공모가</p>
            <p className="text-2xl font-bold">
              ₩{ipo_price_confirmed.toLocaleString()}
            </p>
          </div>

          <div className="p-4 border rounded-lg bg-card">
            <p className="text-sm text-muted-foreground">상장일 최고가</p>
            <p className="text-2xl font-bold text-green-600">
              ₩{predicted_day0_high.toLocaleString()}
            </p>
            <div className="flex items-center gap-1 mt-1">
              {predicted_day0_high_return > 0 ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600" />
              )}
              <p
                className={`text-xs ${
                  predicted_day0_high_return > 0
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {predicted_day0_high_return > 0 ? "+" : ""}
                {predicted_day0_high_return.toFixed(2)}%
              </p>
            </div>
          </div>

          <div className="p-4 border rounded-lg bg-card">
            <p className="text-sm text-muted-foreground">상장일 종가</p>
            <p className="text-2xl font-bold">
              ₩{predicted_day0_close.toLocaleString()}
            </p>
            <div className="flex items-center gap-1 mt-1">
              {predicted_day0_close_return > 0 ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600" />
              )}
              <p
                className={`text-xs ${
                  predicted_day0_close_return > 0
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {predicted_day0_close_return > 0 ? "+" : ""}
                {predicted_day0_close_return.toFixed(2)}%
              </p>
            </div>
          </div>

          <div className="p-4 border rounded-lg bg-card">
            <p className="text-sm text-muted-foreground">상장 다음날 종가</p>
            <p className="text-2xl font-bold">
              ₩{predicted_day1_close.toLocaleString()}
            </p>
            <div className="flex items-center gap-1 mt-1">
              {predicted_day1_close_return > 0 ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600" />
              )}
              <p
                className={`text-xs ${
                  predicted_day1_close_return > 0
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {predicted_day1_close_return > 0 ? "+" : ""}
                {predicted_day1_close_return.toFixed(2)}% (전일 대비)
              </p>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="w-full h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip
                formatter={(value: number) => `₩${value.toLocaleString()}`}
              />
              <Legend />
              <Bar dataKey="value" fill="hsl(var(--primary))" name="가격 (₩)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Expected Returns Summary */}
        <div className="p-4 border rounded-lg bg-muted/50">
          <h3 className="font-semibold mb-3">수익률 비교</h3>
          <div className="space-y-3">
            {/* 상장일 최고 수익률 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <div>
                <p className="text-xs text-muted-foreground mb-1">상장일 최고 수익률 (예상)</p>
                <span
                  className={`text-lg font-semibold ${
                    predicted_day0_high_return > 0
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  {predicted_day0_high_return > 0 ? "+" : ""}
                  {predicted_day0_high_return.toFixed(2)}%
                </span>
              </div>
              {company.actual_day0_high_return !== undefined && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">상장일 최고 수익률 (실제)</p>
                  <span
                    className={`text-lg font-semibold ${
                      company.actual_day0_high_return > 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {company.actual_day0_high_return > 0 ? "+" : ""}
                    {company.actual_day0_high_return.toFixed(2)}%
                  </span>
                  <span className="text-xs text-muted-foreground ml-2">
                    (오차: {Math.abs(predicted_day0_high_return - company.actual_day0_high_return).toFixed(2)}%p)
                  </span>
                </div>
              )}
            </div>

            {/* 상장일 종가 수익률 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-2 border-t">
              <div>
                <p className="text-xs text-muted-foreground mb-1">상장일 종가 수익률 (예상)</p>
                <span
                  className={`text-lg font-semibold ${
                    predicted_day0_close_return > 0
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  {predicted_day0_close_return > 0 ? "+" : ""}
                  {predicted_day0_close_return.toFixed(2)}%
                </span>
              </div>
              {company.actual_day0_close_return !== undefined && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">상장일 종가 수익률 (실제)</p>
                  <span
                    className={`text-lg font-semibold ${
                      company.actual_day0_close_return > 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {company.actual_day0_close_return > 0 ? "+" : ""}
                    {company.actual_day0_close_return.toFixed(2)}%
                  </span>
                  <span className="text-xs text-muted-foreground ml-2">
                    (오차: {Math.abs(predicted_day0_close_return - company.actual_day0_close_return).toFixed(2)}%p)
                  </span>
                </div>
              )}
            </div>

            {/* 다음날 종가 수익률 (상장일 대비) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-2 border-t">
              <div>
                <p className="text-xs text-muted-foreground mb-1">다음날 종가 수익률 (예상, 상장일 대비)</p>
                <span
                  className={`text-lg font-semibold ${
                    predicted_day1_close_return > 0
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  {predicted_day1_close_return > 0 ? "+" : ""}
                  {predicted_day1_close_return.toFixed(2)}%
                </span>
              </div>
              {company.actual_day1_close_return !== undefined && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">다음날 종가 수익률 (실제, 상장일 대비)</p>
                  <span
                    className={`text-lg font-semibold ${
                      company.actual_day1_close_return > 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {company.actual_day1_close_return > 0 ? "+" : ""}
                    {company.actual_day1_close_return.toFixed(2)}%
                  </span>
                  <span className="text-xs text-muted-foreground ml-2">
                    (오차: {Math.abs(predicted_day1_close_return - company.actual_day1_close_return).toFixed(2)}%p)
                  </span>
                </div>
              )}
            </div>

            {/* 다음날 최고가 (실제값만 있음) */}
            {company.actual_day1_high !== undefined && company.actual_day1_high > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-2 border-t">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">다음날 최고 수익률 (실제, 상장일 대비)</p>
                  <span
                    className={`text-lg font-semibold ${
                      (company.actual_day1_high_return || 0) > 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {(company.actual_day1_high_return || 0) > 0 ? "+" : ""}
                    {(company.actual_day1_high_return || 0).toFixed(2)}%
                  </span>
                  <p className="text-xs text-muted-foreground mt-1">
                    ₩{company.actual_day1_high.toLocaleString()}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Stock Chart */}
        <StockChart
          companyName={company_name}
          ipoPrice={ipo_price_confirmed}
          day0Ohlcv={company.day0_ohlcv}
          day1Ohlcv={company.day1_ohlcv}
          day0High={company.actual_day0_high}
          day0Close={company.actual_day0_close}
          day1High={company.actual_day1_high}
          day1Close={company.actual_day1_close}
        />
      </CardContent>
    </Card>
  );
}
