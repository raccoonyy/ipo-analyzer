import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Label,
  Legend,
  Cell,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { IPOCompany } from "@/types/ipo";
import { useState } from "react";

interface ErrorAnalysisChartProps {
  companies: IPOCompany[];
}

interface DataPoint {
  name: string;
  actualReturn: number;
  predictionError: number;
  predictedReturn: number;
  code: string;
  industry: string;
}

type ColorMode = "single" | "industry";

// 업종별 색상 팔레트
const INDUSTRY_COLORS: Record<string, string> = {
  "코스닥": "#ef4444",
  "기술성장기업부": "#f97316",
  "코넥스": "#eab308",
  "기타": "#84cc16",
  "코스피": "#22c55e",
  "스팩": "#14b8a6",
  "벤처기업부": "#06b6d4",
  "중견기업부": "#0ea5e9",
  "우량기업부": "#3b82f6",
  "일반기업부": "#6366f1",
};

export function ErrorAnalysisChart({ companies }: ErrorAnalysisChartProps) {
  const [colorMode, setColorMode] = useState<ColorMode>("single");

  // Filter companies with actual data
  const validCompanies = companies.filter(
    (c) => c.actual_day0_close_return !== undefined
  );

  // Transform data
  const data: DataPoint[] = validCompanies.map((c) => ({
    name: c.company_name,
    actualReturn: c.actual_day0_close_return || 0,
    predictionError: (c.actual_day0_close_return || 0) - c.predicted_day0_close_return,
    predictedReturn: c.predicted_day0_close_return,
    code: c.code,
    industry: c.industry,
  }));

  // Get unique industries for legend
  const industries = Array.from(new Set(data.map(d => d.industry)));

  // Calculate statistics
  const avgError = data.reduce((sum, d) => sum + d.predictionError, 0) / data.length;
  const absErrors = data.map(d => Math.abs(d.predictionError));
  const mae = absErrors.reduce((sum, e) => sum + e, 0) / absErrors.length;

  // Count quadrants
  const underestimated = data.filter(d => d.predictionError > 0).length; // 실제 > 예측
  const overestimated = data.filter(d => d.predictionError < 0).length; // 실제 < 예측

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>예측 오차 분석</CardTitle>
            <CardDescription>
              실제 수익률 대비 예측 오차를 분석합니다. Y=0 선이 완벽한 예측을 의미합니다.
            </CardDescription>
          </div>
          <Select
            value={colorMode}
            onValueChange={(value) => setColorMode(value as ColorMode)}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="single">단일 색상</SelectItem>
              <SelectItem value="industry">업종별 색상</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 border rounded-lg bg-muted/50">
          <div>
            <p className="text-xs text-muted-foreground">분석 기업수</p>
            <p className="text-lg font-semibold">{data.length}개</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">평균 오차</p>
            <p className={`text-lg font-semibold ${avgError > 0 ? 'text-blue-600' : 'text-orange-600'}`}>
              {avgError > 0 ? '+' : ''}{avgError.toFixed(2)}%p
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">평균 절대 오차 (MAE)</p>
            <p className="text-lg font-semibold">{mae.toFixed(2)}%p</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">과대평가 / 과소평가</p>
            <p className="text-lg font-semibold">
              {overestimated} / {underestimated}
            </p>
          </div>
        </div>

        {/* Chart */}
        <div className="w-full h-[500px]">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart
              margin={{ top: 20, right: 20, bottom: 60, left: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                type="number"
                dataKey="actualReturn"
                name="실제 수익률"
                unit="%"
                label={{
                  value: "실제 수익률 (%)",
                  position: "bottom",
                  offset: 40,
                }}
              />
              <YAxis
                type="number"
                dataKey="predictionError"
                name="예측 오차"
                unit="%p"
                label={{
                  value: "예측 오차 (실제 - 예측, %p)",
                  angle: -90,
                  position: "left",
                  offset: 40,
                }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload as DataPoint;
                    return (
                      <div className="bg-background border border-border p-3 rounded shadow-lg">
                        <p className="font-semibold mb-2">
                          {data.name} ({data.code})
                        </p>
                        <div className="space-y-1 text-xs">
                          <p>
                            <span className="text-muted-foreground">실제 수익률:</span>{" "}
                            <span className="font-medium">
                              {data.actualReturn.toFixed(2)}%
                            </span>
                          </p>
                          <p>
                            <span className="text-muted-foreground">예측 수익률:</span>{" "}
                            <span className="font-medium">
                              {data.predictedReturn.toFixed(2)}%
                            </span>
                          </p>
                          <p className="border-t pt-1">
                            <span className="text-muted-foreground">예측 오차:</span>{" "}
                            <span
                              className={`font-medium ${
                                data.predictionError > 0
                                  ? "text-blue-600"
                                  : "text-orange-600"
                              }`}
                            >
                              {data.predictionError > 0 ? "+" : ""}
                              {data.predictionError.toFixed(2)}%p
                            </span>
                            <span className="text-muted-foreground ml-2">
                              ({data.predictionError > 0 ? "과소평가" : "과대평가"})
                            </span>
                          </p>
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend />

              {/* Perfect prediction line */}
              <ReferenceLine
                y={0}
                stroke="#22c55e"
                strokeWidth={2}
                strokeDasharray="5 5"
                label={{
                  value: "완벽한 예측",
                  position: "right",
                  fill: "#22c55e",
                }}
              />

              {/* Underestimation area indicator */}
              <ReferenceLine
                y={0}
                stroke="#3b82f6"
                strokeWidth={0}
                label={{
                  value: "과소평가 ↑",
                  position: "insideTopRight",
                  fill: "#3b82f6",
                  fontSize: 12,
                }}
              />

              {/* Overestimation area indicator */}
              <ReferenceLine
                y={0}
                stroke="#f59e0b"
                strokeWidth={0}
                label={{
                  value: "과대평가 ↓",
                  position: "insideBottomRight",
                  fill: "#f59e0b",
                  fontSize: 12,
                }}
              />

              <Scatter
                name="IPO 기업"
                data={data}
                fill="#8884d8"
                fillOpacity={0.6}
              >
                {data.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={colorMode === "industry"
                      ? INDUSTRY_COLORS[entry.industry] || "#8884d8"
                      : "#8884d8"
                    }
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Industry Legend (when industry mode) */}
        {colorMode === "industry" && (
          <div className="p-4 border rounded-lg bg-muted/50">
            <p className="text-sm font-semibold mb-3">업종별 색상</p>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 text-sm">
              {industries.map((industry) => (
                <div key={industry} className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: INDUSTRY_COLORS[industry] || "#8884d8" }}
                  ></div>
                  <span className="text-xs">{industry}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Interpretation Guide */}
        <div className="p-4 border rounded-lg bg-muted/50 text-sm space-y-2">
          <p className="font-semibold">해석 가이드:</p>
          <ul className="space-y-1 text-muted-foreground">
            <li>• <span className="text-green-600 font-medium">Y=0 선</span>: 예측이 실제와 정확히 일치하는 완벽한 예측</li>
            <li>• <span className="text-blue-600 font-medium">Y &gt; 0 (상단)</span>: 과소평가 - 실제가 예측보다 높음 (숨겨진 기회!)</li>
            <li>• <span className="text-orange-600 font-medium">Y &lt; 0 (하단)</span>: 과대평가 - 실제가 예측보다 낮음 (위험 신호!)</li>
            <li>• 평균 오차가 양수면 모델이 전반적으로 보수적, 음수면 낙관적</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
