import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
  Cell,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { IPOCompany } from "@/types/ipo";
import { useState } from "react";

interface QuadrantChartProps {
  companies: IPOCompany[];
}

interface DataPoint {
  name: string;
  predictedReturn: number;
  actualReturn: number;
  code: string;
  quadrant: number;
  industry: string;
}

type ThresholdType = "zero" | "median" | "mean";
type ColorMode = "quadrant" | "industry";

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

export function QuadrantChart({ companies }: QuadrantChartProps) {
  const [thresholdType, setThresholdType] = useState<ThresholdType>("median");
  const [colorMode, setColorMode] = useState<ColorMode>("quadrant");

  // Filter companies with actual data
  const validCompanies = companies.filter(
    (c) => c.actual_day0_close_return !== undefined
  );

  // Calculate thresholds
  const predictedReturns = validCompanies.map((c) => c.predicted_day0_close_return);
  const actualReturns = validCompanies.map((c) => c.actual_day0_close_return || 0);

  const predMedian = [...predictedReturns].sort((a, b) => a - b)[
    Math.floor(predictedReturns.length / 2)
  ];
  const actualMedian = [...actualReturns].sort((a, b) => a - b)[
    Math.floor(actualReturns.length / 2)
  ];

  const predMean = predictedReturns.reduce((a, b) => a + b, 0) / predictedReturns.length;
  const actualMean = actualReturns.reduce((a, b) => a + b, 0) / actualReturns.length;

  // Select threshold based on type
  const predThreshold =
    thresholdType === "zero" ? 0 : thresholdType === "median" ? predMedian : predMean;
  const actualThreshold =
    thresholdType === "zero" ? 0 : thresholdType === "median" ? actualMedian : actualMean;

  // Transform data with quadrant assignment
  const data: DataPoint[] = validCompanies.map((c) => {
    const pred = c.predicted_day0_close_return;
    const actual = c.actual_day0_close_return || 0;

    let quadrant: number;
    if (pred >= predThreshold && actual >= actualThreshold) quadrant = 1; // Q1
    else if (pred < predThreshold && actual >= actualThreshold) quadrant = 2; // Q2
    else if (pred < predThreshold && actual < actualThreshold) quadrant = 3; // Q3
    else quadrant = 4; // Q4

    return {
      name: c.company_name,
      predictedReturn: pred,
      actualReturn: actual,
      code: c.code,
      quadrant,
      industry: c.industry,
    };
  });

  // Count quadrants
  const quadrantCounts = {
    q1: data.filter((d) => d.quadrant === 1).length,
    q2: data.filter((d) => d.quadrant === 2).length,
    q3: data.filter((d) => d.quadrant === 3).length,
    q4: data.filter((d) => d.quadrant === 4).length,
  };

  // Colors for quadrants
  const quadrantColors: Record<number, string> = {
    1: "#22c55e", // Green
    2: "#eab308", // Yellow
    3: "#ef4444", // Red
    4: "#f97316", // Orange
  };

  // Get unique industries for legend
  const industries = Array.from(new Set(data.map(d => d.industry)));

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>4분면 분석</CardTitle>
            <CardDescription>
              예측 수익률과 실제 수익률을 4개 분면에 배치합니다
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Select
              value={thresholdType}
              onValueChange={(value) => setThresholdType(value as ThresholdType)}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="zero">0% 기준</SelectItem>
                <SelectItem value="median">중앙값 기준</SelectItem>
                <SelectItem value="mean">평균 기준</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={colorMode}
              onValueChange={(value) => setColorMode(value as ColorMode)}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="quadrant">분면별 색상</SelectItem>
                <SelectItem value="industry">업종별 색상</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 p-4 border rounded-lg bg-muted/50">
          <div>
            <p className="text-xs text-muted-foreground">분석 기업수</p>
            <p className="text-lg font-semibold">{data.length}개</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Q1 (둘 다 높음)</p>
            <p className="text-lg font-semibold text-green-600">
              {quadrantCounts.q1} ({((quadrantCounts.q1 / data.length) * 100).toFixed(1)}%)
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Q2 (예측↓ 실제↑)</p>
            <p className="text-lg font-semibold text-yellow-600">
              {quadrantCounts.q2} ({((quadrantCounts.q2 / data.length) * 100).toFixed(1)}%)
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Q3 (둘 다 낮음)</p>
            <p className="text-lg font-semibold text-red-600">
              {quadrantCounts.q3} ({((quadrantCounts.q3 / data.length) * 100).toFixed(1)}%)
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Q4 (예측↑ 실제↓)</p>
            <p className="text-lg font-semibold text-orange-600">
              {quadrantCounts.q4} ({((quadrantCounts.q4 / data.length) * 100).toFixed(1)}%)
            </p>
          </div>
        </div>

        {/* Threshold Info */}
        <div className="p-3 border rounded-lg bg-muted/50 text-sm">
          <p className="font-semibold mb-1">기준값:</p>
          <div className="grid grid-cols-2 gap-2 text-muted-foreground">
            <p>예측 수익률: <span className="font-medium text-foreground">{predThreshold.toFixed(2)}%</span></p>
            <p>실제 수익률: <span className="font-medium text-foreground">{actualThreshold.toFixed(2)}%</span></p>
          </div>
        </div>

        {/* Chart */}
        <div className="w-full h-[500px]">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 20, bottom: 60, left: 60 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                type="number"
                dataKey="predictedReturn"
                name="예측 수익률"
                unit="%"
                label={{
                  value: "예측 수익률 (%)",
                  position: "bottom",
                  offset: 40,
                }}
              />
              <YAxis
                type="number"
                dataKey="actualReturn"
                name="실제 수익률"
                unit="%"
                label={{
                  value: "실제 수익률 (%)",
                  angle: -90,
                  position: "left",
                  offset: 40,
                }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload as DataPoint;
                    const quadrantNames = {
                      1: "Q1 (둘 다 높음)",
                      2: "Q2 (예측 낮음, 실제 높음)",
                      3: "Q3 (둘 다 낮음)",
                      4: "Q4 (예측 높음, 실제 낮음)",
                    };
                    return (
                      <div className="bg-background border border-border p-3 rounded shadow-lg">
                        <p className="font-semibold mb-2">
                          {data.name} ({data.code})
                        </p>
                        <div className="space-y-1 text-xs">
                          <p>
                            <span className="text-muted-foreground">예측 수익률:</span>{" "}
                            <span className="font-medium">
                              {data.predictedReturn.toFixed(2)}%
                            </span>
                          </p>
                          <p>
                            <span className="text-muted-foreground">실제 수익률:</span>{" "}
                            <span className="font-medium">
                              {data.actualReturn.toFixed(2)}%
                            </span>
                          </p>
                          <p className="border-t pt-1">
                            <span className="text-muted-foreground">분면:</span>{" "}
                            <span
                              className="font-medium"
                              style={{ color: quadrantColors[data.quadrant] }}
                            >
                              {quadrantNames[data.quadrant as keyof typeof quadrantNames]}
                            </span>
                          </p>
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />

              {/* Reference lines */}
              <ReferenceLine
                x={predThreshold}
                stroke="#666"
                strokeWidth={2}
                strokeDasharray="5 5"
              />
              <ReferenceLine
                y={actualThreshold}
                stroke="#666"
                strokeWidth={2}
                strokeDasharray="5 5"
              />

              {/* Quadrant labels */}
              <ReferenceLine
                x={predThreshold}
                y={actualThreshold}
                stroke="transparent"
                label={{
                  value: "Q2",
                  position: "insideTopLeft",
                  fill: "#eab308",
                  fontSize: 14,
                  fontWeight: "bold",
                }}
              />
              <ReferenceLine
                x={predThreshold}
                y={actualThreshold}
                stroke="transparent"
                label={{
                  value: "Q1",
                  position: "insideTopRight",
                  fill: "#22c55e",
                  fontSize: 14,
                  fontWeight: "bold",
                }}
              />
              <ReferenceLine
                x={predThreshold}
                y={actualThreshold}
                stroke="transparent"
                label={{
                  value: "Q3",
                  position: "insideBottomLeft",
                  fill: "#ef4444",
                  fontSize: 14,
                  fontWeight: "bold",
                }}
              />
              <ReferenceLine
                x={predThreshold}
                y={actualThreshold}
                stroke="transparent"
                label={{
                  value: "Q4",
                  position: "insideBottomRight",
                  fill: "#f97316",
                  fontSize: 14,
                  fontWeight: "bold",
                }}
              />

              <Scatter name="IPO 기업" data={data} fillOpacity={0.6}>
                {data.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={colorMode === "industry"
                      ? INDUSTRY_COLORS[entry.industry] || "#8884d8"
                      : quadrantColors[entry.quadrant]
                    }
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        {colorMode === "quadrant" && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 border rounded-lg bg-muted/50 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: "#22c55e" }}></div>
              <span>Q1: 모두 높음</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: "#eab308" }}></div>
              <span>Q2: 과소평가</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: "#ef4444" }}></div>
              <span>Q3: 모두 낮음</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: "#f97316" }}></div>
              <span>Q4: 과대평가</span>
            </div>
          </div>
        )}

        {/* Industry Legend */}
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
      </CardContent>
    </Card>
  );
}
