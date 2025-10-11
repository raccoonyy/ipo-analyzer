import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Calculator as CalculatorIcon, BarChart3, Home, AlertCircle } from "lucide-react";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  Cell,
  CartesianGrid,
} from "recharts";

interface CalculatorData {
  metadata: {
    total_samples: number;
    overall_mean_return: number;
    overall_median_return: number;
    data_period: string;
  };
  heatmap_data: Array<{
    competition: string;
    lockup: string;
    mean_return: number | null;
    median_return: number | null;
    std_return: number | null;
    count: number;
  }>;
  price_factors: Record<
    string,
    {
      factor: number;
      mean_return: number;
      count: number;
    }
  >;
  top_combinations: Array<{
    competition: string;
    lockup: string;
    expected_return: number;
    sample_count: number;
  }>;
}

const Calculator = () => {
  const [ipoPrice, setIpoPrice] = useState([20000]);
  const [competitionRate, setCompetitionRate] = useState([1000]);
  const [lockupRatio, setLockupRatio] = useState([50]);
  const [calculatorData, setCalculatorData] = useState<CalculatorData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}calculator_data.json`)
      .then((res) => res.json())
      .then((data: CalculatorData) => {
        setCalculatorData(data);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load calculator data:", err);
        setIsLoading(false);
      });
  }, []);

  const calculateExpectedReturn = (): {
    expected: number;
    lower: number;
    upper: number;
    confidence: string;
    sampleCount: number;
  } => {
    if (!calculatorData) return { expected: 0, lower: 0, upper: 0, confidence: "low", sampleCount: 0 };

    const price = ipoPrice[0];
    const comp = competitionRate[0];
    const lockup = lockupRatio[0];

    // Determine bins
    let compBin = "Low (<500)";
    if (comp >= 2000) compBin = "Very High (>2K)";
    else if (comp >= 1000) compBin = "High (1K-2K)";
    else if (comp >= 500) compBin = "Medium (500-1K)";

    let lockupBin = "Low (<30%)";
    if (lockup >= 60) lockupBin = "High (>60%)";
    else if (lockup >= 30) lockupBin = "Medium (30-60%)";

    // Find matching heatmap data
    const match = calculatorData.heatmap_data.find(
      (d) => d.competition === compBin && d.lockup === lockupBin
    );

    let baseReturn = calculatorData.metadata.overall_mean_return;
    let stdDev = 50; // default
    let sampleCount = 0;

    if (match && match.count > 0 && match.mean_return !== null) {
      baseReturn = match.mean_return;
      stdDev = match.std_return || 50;
      sampleCount = match.count;
    }

    // Apply price factor
    let priceFactor = 1.0;
    if (price <= 10000) priceFactor = calculatorData.price_factors["0-10K"]?.factor || 1.0;
    else if (price <= 20000) priceFactor = calculatorData.price_factors["10-20K"]?.factor || 1.0;
    else if (price <= 50000) priceFactor = calculatorData.price_factors["20-50K"]?.factor || 1.0;
    else priceFactor = calculatorData.price_factors["50K+"]?.factor || 1.0;

    const adjustedReturn = baseReturn * priceFactor;

    // Calculate confidence interval
    const lower = adjustedReturn - stdDev;
    const upper = adjustedReturn + stdDev;

    // Confidence level based on sample count
    let confidence = "low";
    if (sampleCount >= 20) confidence = "high";
    else if (sampleCount >= 10) confidence = "medium";

    return {
      expected: adjustedReturn,
      lower,
      upper,
      confidence,
      sampleCount,
    };
  };

  const result = calculateExpectedReturn();

  // Prepare heatmap data for chart
  const heatmapChartData =
    calculatorData?.heatmap_data
      .filter((d) => d.count > 0 && d.mean_return !== null)
      .map((d) => {
        // Map competition to numeric
        let compValue = 250;
        if (d.competition === "Medium (500-1K)") compValue = 750;
        else if (d.competition === "High (1K-2K)") compValue = 1500;
        else if (d.competition === "Very High (>2K)") compValue = 2500;

        // Map lockup to numeric
        let lockupValue = 15;
        if (d.lockup === "Medium (30-60%)") lockupValue = 45;
        else if (d.lockup === "High (>60%)") lockupValue = 75;

        return {
          x: compValue,
          y: lockupValue,
          z: d.mean_return,
          label: `${d.competition.split(" ")[0]} + ${d.lockup.split(" ")[0]}`,
          count: d.count,
        };
      }) || [];

  const getReturnColor = (returnValue: number): string => {
    if (returnValue >= 80) return "#22c55e"; // green-500
    if (returnValue >= 50) return "#84cc16"; // lime-500
    if (returnValue >= 30) return "#eab308"; // yellow-500
    if (returnValue >= 15) return "#f97316"; // orange-500
    return "#ef4444"; // red-500
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>로딩 중...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CalculatorIcon className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-3xl font-bold">기대 수익률 계산하기</h1>
                <p className="text-muted-foreground mt-1">
                  실제 데이터 기반 IPO 수익률 예측 ({calculatorData?.metadata.total_samples}건)
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Link to="/">
                <Button variant="outline" className="gap-2">
                  <Home className="h-4 w-4" />
                  예측
                </Button>
              </Link>
              <Link to="/analysis">
                <Button variant="outline" className="gap-2">
                  <BarChart3 className="h-4 w-4" />
                  분석
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Section */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>IPO 조건 입력</CardTitle>
                <CardDescription>예상하는 IPO 조건을 입력하세요</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* IPO Price */}
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <label className="text-sm font-medium">확정공모가</label>
                    <span className="text-sm font-bold text-primary">
                      ₩{ipoPrice[0].toLocaleString()}
                    </span>
                  </div>
                  <Slider
                    value={ipoPrice}
                    onValueChange={setIpoPrice}
                    min={1000}
                    max={100000}
                    step={1000}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>₩1,000</span>
                    <span>₩100,000</span>
                  </div>
                </div>

                {/* Competition Rate */}
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <label className="text-sm font-medium">청약경쟁률</label>
                    <span className="text-sm font-bold text-primary">
                      {competitionRate[0].toLocaleString()}:1
                    </span>
                  </div>
                  <Slider
                    value={competitionRate}
                    onValueChange={setCompetitionRate}
                    min={0}
                    max={3000}
                    step={50}
                    className="w-full"
                  />
                  <div className="relative flex justify-between text-xs text-muted-foreground">
                    <span>0:1</span>
                    <span className="absolute left-[16.67%] -translate-x-1/2">500:1</span>
                    <span className="absolute left-[33.33%] -translate-x-1/2">1,000:1</span>
                    <span className="absolute left-[66.67%] -translate-x-1/2">2,000:1</span>
                    <span>3,000:1</span>
                  </div>
                </div>

                {/* Lockup Ratio */}
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <label className="text-sm font-medium">의무보유확약비율</label>
                    <span className="text-sm font-bold text-primary">
                      {lockupRatio[0]}%
                    </span>
                  </div>
                  <Slider
                    value={lockupRatio}
                    onValueChange={setLockupRatio}
                    min={0}
                    max={100}
                    step={5}
                    className="w-full"
                  />
                  <div className="relative flex justify-between text-xs text-muted-foreground">
                    <span>0%</span>
                    <span className="absolute left-[30%] -translate-x-1/2">30%</span>
                    <span className="absolute left-[60%] -translate-x-1/2">60%</span>
                    <span>100%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Result Section */}
            <Card>
              <CardHeader>
                <CardTitle>예상 수익률</CardTitle>
                <CardDescription>상장일+1일 종가 기준</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center p-6 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground mb-2">기대 수익률</p>
                  <p
                    className={`text-5xl font-bold ${
                      result.expected >= 0 ? "text-green-600" : "text-red-600"
                    }`}
                  >
                    {result.expected >= 0 ? "+" : ""}
                    {result.expected.toFixed(1)}%
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">신뢰구간 (±1σ)</span>
                    <span className="font-medium">
                      {result.lower.toFixed(1)}% ~ {result.upper.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">신뢰도 (샘플 수)</span>
                    <span
                      className={`font-medium ${
                        result.confidence === "high"
                          ? "text-green-600"
                          : result.confidence === "medium"
                          ? "text-yellow-600"
                          : "text-orange-600"
                      }`}
                    >
                      {result.confidence === "high"
                        ? "높음"
                        : result.confidence === "medium"
                        ? "중간"
                        : "낮음"}{" "}
                      ({result.sampleCount}건)
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-muted rounded-md border">
                  <p className="text-xs text-muted-foreground">
                    💡 <strong>신뢰구간</strong>: 실제 수익률이 이 범위에 포함될 확률이 약 68%입니다.
                    <br />
                    💡 <strong>신뢰도</strong>: 높음(20건 이상), 중간(10-19건), 낮음(10건 미만). 샘플이 많을수록 예측이 정확합니다.
                  </p>
                </div>

                <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-md border border-blue-200 dark:border-blue-800">
                  <div className="flex gap-2">
                    <AlertCircle className="h-4 w-4 text-blue-600 mt-0.5" />
                    <p className="text-xs text-blue-900 dark:text-blue-100">
                      이 예측은 과거 데이터를 기반으로 한 참고용이며, 실제 수익을 보장하지 않습니다.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Visualization Section */}
          <div className="space-y-6">
            {/* Heatmap */}
            <Card>
              <CardHeader>
                <CardTitle>조합별 평균 수익률</CardTitle>
                <CardDescription>청약경쟁률 × 의무보유확약비율</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      type="number"
                      dataKey="x"
                      name="청약경쟁률"
                      label={{ value: "청약경쟁률", position: "bottom" }}
                      domain={[0, 3000]}
                    />
                    <YAxis
                      type="number"
                      dataKey="y"
                      name="의무보유비율"
                      label={{ value: "의무보유비율 (%)", angle: -90, position: "left" }}
                      domain={[0, 100]}
                    />
                    <ZAxis type="number" dataKey="z" range={[400, 1000]} />
                    <Tooltip
                      cursor={{ strokeDasharray: "3 3" }}
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="bg-background border rounded p-2 shadow-lg">
                              <p className="font-semibold">{data.label}</p>
                              <p className="text-sm">수익률: {data.z.toFixed(1)}%</p>
                              <p className="text-xs text-muted-foreground">
                                샘플: {data.count}건
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Scatter data={heatmapChartData}>
                      {heatmapChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getReturnColor(entry.z)} />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Top Combinations */}
            <Card>
              <CardHeader>
                <CardTitle>수익률 높은 조합 TOP 5</CardTitle>
                <CardDescription>
                  청약경쟁률 × 의무보유비율 조합 (실제 데이터 기반)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {calculatorData?.top_combinations.map((combo, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-muted rounded-lg"
                    >
                      <div className="flex-1">
                        <p className="text-sm font-medium">
                          {idx + 1}. {combo.competition} 경쟁률 + {combo.lockup} 의무보유
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {combo.sample_count}건 샘플
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-green-600">
                          +{combo.expected_return.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 p-3 bg-muted rounded-md border">
                  <p className="text-xs text-muted-foreground">
                    💡 <strong>구간 설명</strong>
                    <br />
                    • Low/Medium/High/Very High: 청약경쟁률 구간 (Low &lt;500, Medium 500-1K, High 1K-2K, Very High &gt;2K)
                    <br />
                    • Low/Medium/High: 의무보유비율 구간 (Low &lt;30%, Medium 30-60%, High &gt;60%)
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Disclaimer */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-lg">⚠️ 주의사항</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                • 이 계산기는 {calculatorData?.metadata.data_period} 기간의{" "}
                {calculatorData?.metadata.total_samples}건 IPO 데이터를 기반으로 합니다.
              </li>
              <li>• 과거 데이터 분석 결과이며, 미래 수익을 보장하지 않습니다.</li>
              <li>
                • 실제 수익률은 시장 상황, 기업 특성, 업종 등 다양한 요인에 영향을 받습니다.
              </li>
              <li>• 투자 결정 시 반드시 추가적인 조사와 분석을 수행하세요.</li>
              <li>• 모든 투자 결정과 그 결과는 투자자 본인의 책임입니다.</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Calculator;
