import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { OHLCVData } from "@/types/ipo";

interface StockChartProps {
  companyName: string;
  ipoPrice: number;
  day0Ohlcv?: OHLCVData[];
  day1Ohlcv?: OHLCVData[];
  // 폴백: OHLCV 데이터가 없을 때 사용할 기본 데이터
  day0High?: number;
  day0Close?: number;
  day1Close?: number;
}

export function StockChart({
  companyName,
  ipoPrice,
  day0Ohlcv,
  day1Ohlcv,
  day0High,
  day0Close,
  day1Close,
}: StockChartProps) {
  // 상장일과 다음날 데이터를 합침
  const allData: OHLCVData[] = [];

  if (day0Ohlcv) {
    allData.push(...day0Ohlcv);
  }

  if (day1Ohlcv) {
    allData.push(...day1Ohlcv);
  }

  // OHLCV 데이터가 없으면 기본 데이터로 폴백
  if (allData.length === 0) {
    if (day0High && day0Close) {
      allData.push({
        timestamp: "상장일",
        open: ipoPrice,
        high: day0High,
        low: Math.min(ipoPrice, day0Close),
        close: day0Close,
        volume: 0,
      });
    }
    if (day1Close) {
      allData.push({
        timestamp: "상장 다음날",
        open: day0Close || ipoPrice,
        high: day1Close,
        low: day1Close,
        close: day1Close,
        volume: 0,
      });
    }
  }

  // 데이터가 하나도 없으면 표시하지 않음
  if (allData.length === 0) {
    return null;
  }

  // 거래량의 최대값을 구해서 스케일 조정
  const maxVolume = Math.max(...allData.map(d => d.volume), 1);
  const hasVolumeData = maxVolume > 0;

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{companyName} - 실제 주가 차트</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* OHLCV Chart with Volume */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-medium">주가{hasVolumeData ? " 및 거래량" : ""}</h3>
            <p className="text-xs text-muted-foreground">
              공모가: ₩{ipoPrice.toLocaleString()}
            </p>
          </div>
          <div className="w-full h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={allData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tick={{ fontSize: 11 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                {/* 왼쪽 Y축: 가격 */}
                <YAxis
                  yAxisId="price"
                  orientation="left"
                  stroke="#8884d8"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `₩${(value / 1000).toFixed(0)}k`}
                />
                {/* 오른쪽 Y축: 거래량 (거래량 데이터가 있을 때만) */}
                {hasVolumeData && (
                  <YAxis
                    yAxisId="volume"
                    orientation="right"
                    stroke="#82ca9d"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`}
                  />
                )}
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload as OHLCVData;
                      return (
                        <div className="bg-background border border-border p-3 rounded shadow-lg">
                          <p className="font-semibold mb-2">{data.timestamp}</p>
                          <div className="space-y-1 text-xs">
                            <p>
                              <span className="text-muted-foreground">시가:</span>{" "}
                              <span className="font-medium">
                                ₩{data.open.toLocaleString()}
                              </span>
                            </p>
                            <p>
                              <span className="text-muted-foreground">고가:</span>{" "}
                              <span className="font-medium text-red-600">
                                ₩{data.high.toLocaleString()}
                              </span>
                            </p>
                            <p>
                              <span className="text-muted-foreground">저가:</span>{" "}
                              <span className="font-medium text-blue-600">
                                ₩{data.low.toLocaleString()}
                              </span>
                            </p>
                            <p>
                              <span className="text-muted-foreground">종가:</span>{" "}
                              <span className="font-medium">
                                ₩{data.close.toLocaleString()}
                              </span>
                            </p>
                            {hasVolumeData && (
                              <p className="border-t pt-1 mt-1">
                                <span className="text-muted-foreground">거래량:</span>{" "}
                                <span className="font-medium">
                                  {data.volume.toLocaleString()}주
                                </span>
                              </p>
                            )}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend />

                {/* 거래량 막대 (거래량 데이터가 있을 때만) */}
                {hasVolumeData && (
                  <Bar
                    yAxisId="volume"
                    dataKey="volume"
                    fill="#82ca9d"
                    opacity={0.3}
                    name="거래량"
                  />
                )}

                {/* 가격 선 그래프 */}
                <Line
                  yAxisId="price"
                  type="monotone"
                  dataKey="high"
                  stroke="#ef4444"
                  strokeWidth={1.5}
                  dot={false}
                  name="고가"
                />
                <Line
                  yAxisId="price"
                  type="monotone"
                  dataKey="low"
                  stroke="#3b82f6"
                  strokeWidth={1.5}
                  dot={false}
                  name="저가"
                />
                <Line
                  yAxisId="price"
                  type="monotone"
                  dataKey="close"
                  stroke="#8884d8"
                  strokeWidth={2}
                  dot={false}
                  name="종가"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Summary Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 border rounded-lg bg-muted/50">
          <div>
            <p className="text-xs text-muted-foreground">시작가</p>
            <p className="text-sm font-semibold">
              ₩{allData[0]?.open.toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">최고가</p>
            <p className="text-sm font-semibold text-red-600">
              ₩{Math.max(...allData.map(d => d.high)).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">최저가</p>
            <p className="text-sm font-semibold text-blue-600">
              ₩{Math.min(...allData.map(d => d.low)).toLocaleString()}
            </p>
          </div>
          {hasVolumeData && (
            <div>
              <p className="text-xs text-muted-foreground">총 거래량</p>
              <p className="text-sm font-semibold">
                {allData.reduce((sum, d) => sum + d.volume, 0).toLocaleString()}주
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
