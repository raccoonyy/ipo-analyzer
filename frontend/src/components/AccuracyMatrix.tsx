import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { IPOCompany } from "@/types/ipo";

interface AccuracyMatrixProps {
  companies: IPOCompany[];
}

export function AccuracyMatrix({ companies }: AccuracyMatrixProps) {
  // Filter companies with actual data
  const validCompanies = companies.filter(
    (c) => c.actual_day0_close_return !== undefined
  );

  // Calculate confusion matrix
  let truePositive = 0; // 예측+, 실제+
  let trueNegative = 0; // 예측-, 실제-
  let falsePositive = 0; // 예측+, 실제-
  let falseNegative = 0; // 예측-, 실제+

  validCompanies.forEach((c) => {
    const predicted = c.predicted_day0_close_return >= 0;
    const actual = (c.actual_day0_close_return || 0) >= 0;

    if (predicted && actual) truePositive++;
    else if (!predicted && !actual) trueNegative++;
    else if (predicted && !actual) falsePositive++;
    else if (!predicted && actual) falseNegative++;
  });

  const total = validCompanies.length;

  // Calculate metrics
  const accuracy = ((truePositive + trueNegative) / total) * 100;
  const precision = truePositive / (truePositive + falsePositive) * 100;
  const recall = truePositive / (truePositive + falseNegative) * 100;
  const f1Score = (2 * precision * recall) / (precision + recall);

  // Calculate hit rate for negative predictions
  const negativePrecision = trueNegative / (trueNegative + falseNegative) * 100;

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>방향 예측 정확도</CardTitle>
        <CardDescription>
          예측 방향(+/-)과 실제 방향(+/-)의 일치율을 분석합니다
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Confusion Matrix */}
        <div className="space-y-2">
          <p className="text-sm font-semibold">Confusion Matrix</p>
          <div className="grid grid-cols-[auto_1fr_1fr] gap-2 text-sm">
            {/* Header row */}
            <div></div>
            <div className="font-semibold text-center p-2 bg-muted rounded">
              실제 플러스 (+)
            </div>
            <div className="font-semibold text-center p-2 bg-muted rounded">
              실제 마이너스 (-)
            </div>

            {/* Predicted Positive row */}
            <div className="font-semibold p-2 bg-muted rounded flex items-center justify-center">
              예측<br/>플러스<br/>(+)
            </div>
            <div className="p-4 border-2 border-green-500 rounded-lg bg-green-50 dark:bg-green-950 text-center">
              <p className="text-2xl font-bold text-green-700 dark:text-green-300">
                {truePositive}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                True Positive
              </p>
              <p className="text-xs text-muted-foreground">
                ({((truePositive / total) * 100).toFixed(1)}%)
              </p>
            </div>
            <div className="p-4 border-2 border-orange-500 rounded-lg bg-orange-50 dark:bg-orange-950 text-center">
              <p className="text-2xl font-bold text-orange-700 dark:text-orange-300">
                {falsePositive}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                False Positive
              </p>
              <p className="text-xs text-muted-foreground">
                ({((falsePositive / total) * 100).toFixed(1)}%)
              </p>
            </div>

            {/* Predicted Negative row */}
            <div className="font-semibold p-2 bg-muted rounded flex items-center justify-center">
              예측<br/>마이너스<br/>(-)
            </div>
            <div className="p-4 border-2 border-yellow-500 rounded-lg bg-yellow-50 dark:bg-yellow-950 text-center">
              <p className="text-2xl font-bold text-yellow-700 dark:text-yellow-300">
                {falseNegative}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                False Negative
              </p>
              <p className="text-xs text-muted-foreground">
                ({((falseNegative / total) * 100).toFixed(1)}%)
              </p>
            </div>
            <div className="p-4 border-2 border-blue-500 rounded-lg bg-blue-50 dark:bg-blue-950 text-center">
              <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                {trueNegative}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                True Negative
              </p>
              <p className="text-xs text-muted-foreground">
                ({((trueNegative / total) * 100).toFixed(1)}%)
              </p>
            </div>
          </div>
        </div>

        {/* Metrics */}
        <div className="space-y-2">
          <p className="text-sm font-semibold">성능 지표</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 border rounded-lg bg-card">
              <p className="text-xs text-muted-foreground">정확도 (Accuracy)</p>
              <p className="text-2xl font-bold">{accuracy.toFixed(1)}%</p>
              <p className="text-xs text-muted-foreground mt-1">
                전체 중 맞춘 비율
              </p>
            </div>
            <div className="p-4 border rounded-lg bg-card">
              <p className="text-xs text-muted-foreground">정밀도 (Precision)</p>
              <p className="text-2xl font-bold">{precision.toFixed(1)}%</p>
              <p className="text-xs text-muted-foreground mt-1">
                + 예측 중 실제 +
              </p>
            </div>
            <div className="p-4 border rounded-lg bg-card">
              <p className="text-xs text-muted-foreground">재현율 (Recall)</p>
              <p className="text-2xl font-bold">{recall.toFixed(1)}%</p>
              <p className="text-xs text-muted-foreground mt-1">
                실제 + 중 예측 +
              </p>
            </div>
            <div className="p-4 border rounded-lg bg-card">
              <p className="text-xs text-muted-foreground">F1 Score</p>
              <p className="text-2xl font-bold">{f1Score.toFixed(1)}%</p>
              <p className="text-xs text-muted-foreground mt-1">
                정밀도·재현율 조화평균
              </p>
            </div>
          </div>
        </div>

        {/* Additional Insights */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 border rounded-lg bg-muted/50">
            <p className="text-sm font-semibold mb-2">플러스(+) 예측 성능</p>
            <div className="space-y-1 text-sm">
              <p>
                <span className="text-muted-foreground">전체 플러스 예측:</span>{" "}
                <span className="font-medium">
                  {truePositive + falsePositive}개
                </span>
              </p>
              <p>
                <span className="text-muted-foreground">실제로 플러스:</span>{" "}
                <span className="font-medium text-green-600">
                  {truePositive}개 ({precision.toFixed(1)}%)
                </span>
              </p>
              <p>
                <span className="text-muted-foreground">실제로 마이너스:</span>{" "}
                <span className="font-medium text-orange-600">
                  {falsePositive}개 ({((falsePositive / (truePositive + falsePositive)) * 100).toFixed(1)}%)
                </span>
              </p>
            </div>
          </div>

          <div className="p-4 border rounded-lg bg-muted/50">
            <p className="text-sm font-semibold mb-2">마이너스(-) 예측 성능</p>
            <div className="space-y-1 text-sm">
              <p>
                <span className="text-muted-foreground">전체 마이너스 예측:</span>{" "}
                <span className="font-medium">
                  {trueNegative + falseNegative}개
                </span>
              </p>
              <p>
                <span className="text-muted-foreground">실제로 마이너스:</span>{" "}
                <span className="font-medium text-blue-600">
                  {trueNegative}개 ({negativePrecision.toFixed(1)}%)
                </span>
              </p>
              <p>
                <span className="text-muted-foreground">실제로 플러스:</span>{" "}
                <span className="font-medium text-yellow-600">
                  {falseNegative}개 ({((falseNegative / (trueNegative + falseNegative)) * 100).toFixed(1)}%)
                </span>
              </p>
            </div>
          </div>
        </div>

        {/* Interpretation Guide */}
        <div className="p-4 border rounded-lg bg-muted/50 text-sm space-y-2">
          <p className="font-semibold">해석 가이드:</p>
          <ul className="space-y-1 text-muted-foreground">
            <li>• <span className="text-green-600 font-medium">True Positive</span>: 플러스 수익 예측이 맞음 (성공)</li>
            <li>• <span className="text-blue-600 font-medium">True Negative</span>: 마이너스 수익 예측이 맞음 (손실 회피)</li>
            <li>• <span className="text-orange-600 font-medium">False Positive</span>: 플러스 예측했지만 실제 마이너스 (Type I 오류)</li>
            <li>• <span className="text-yellow-600 font-medium">False Negative</span>: 마이너스 예측했지만 실제 플러스 (기회 손실)</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
