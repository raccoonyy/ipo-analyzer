import { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import { IPODataResponse, IPOCompany } from "@/types/ipo";
import { IPOFilters, FilterState } from "@/components/IPOFilters";
import { ErrorAnalysisChart } from "@/components/ErrorAnalysisChart";
import { QuadrantChart } from "@/components/QuadrantChart";
import { AccuracyMatrix } from "@/components/AccuracyMatrix";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, BarChart3, ArrowLeft } from "lucide-react";

export default function Analysis() {
  const [ipoData, setIpoData] = useState<IPOCompany[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState<FilterState | null>(null);

  // Load IPO data
  useEffect(() => {
    setIsLoading(true);
    fetch(`${import.meta.env.BASE_URL}ipo_precomputed.json`)
      .then((response) => response.json())
      .then((response: IPODataResponse) => {
        if (!response.ipos || !Array.isArray(response.ipos)) {
          throw new Error("Invalid data format: expected ipos array");
        }
        // Filter only companies with actual data
        const withActualData = response.ipos.filter(
          (ipo) => ipo.actual_day0_close_return !== undefined
        );
        // Filter out SPAC companies
        const filteredIpos = withActualData.filter(
          (ipo) =>
            !ipo.company_name.includes('기업인수목적') &&
            !(ipo.industry && ipo.industry.includes('SPAC'))
        );
        setIpoData(filteredIpos);
      })
      .catch((error) => {
        console.error("Failed to load IPO data:", error);
        setIpoData([]);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  // Filter data based on current filters
  const filteredData = useMemo(() => {
    if (!filters) return ipoData;

    return ipoData.filter((company) => {
      // Date filter
      const listingDate = company.listing_date;
      if (
        listingDate < filters.dateRange.start ||
        listingDate > filters.dateRange.end
      ) {
        return false;
      }

      // Industry filter
      if (
        filters.industries.length > 0 &&
        !filters.industries.includes(company.industry)
      ) {
        return false;
      }

      // Sector 38 filter
      if (
        filters.sectors_38.length > 0 &&
        !filters.sectors_38.includes(company.sector_38)
      ) {
        return false;
      }

      // Price filter
      if (
        company.ipo_price_confirmed < filters.priceRange.min ||
        company.ipo_price_confirmed > filters.priceRange.max
      ) {
        return false;
      }

      return true;
    });
  }, [ipoData, filters]);

  // Calculate summary statistics
  const stats = useMemo(() => {
    if (filteredData.length === 0) {
      return {
        count: 0,
        avgPredicted: 0,
        avgActual: 0,
        avgError: 0,
      };
    }

    const predicted = filteredData.map((c) => c.predicted_day0_close_return);
    const actual = filteredData.map((c) => c.actual_day0_close_return || 0);
    const errors = filteredData.map(
      (c) => (c.actual_day0_close_return || 0) - c.predicted_day0_close_return
    );

    return {
      count: filteredData.length,
      avgPredicted:
        predicted.reduce((a, b) => a + b, 0) / predicted.length,
      avgActual: actual.reduce((a, b) => a + b, 0) / actual.length,
      avgError: errors.reduce((a, b) => a + b, 0) / errors.length,
    };
  }, [filteredData]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-8 w-8 text-primary" />
              <h1 className="text-4xl font-bold">IPO 분석</h1>
            </div>
            <Link to="/">
              <Button variant="outline" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                예측 페이지
              </Button>
            </Link>
          </div>
          <p className="text-lg text-muted-foreground">
            예측 모델의 성능을 다양한 관점에서 분석합니다
          </p>
        </div>

        {/* Summary Statistics */}
        <Card>
          <CardHeader>
            <CardTitle>요약 통계</CardTitle>
            <CardDescription>
              필터링된 {stats.count}개 기업의 통계 정보
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 border rounded-lg bg-card">
                <p className="text-xs text-muted-foreground">분석 기업수</p>
                <p className="text-2xl font-bold">{stats.count}개</p>
              </div>
              <div className="p-4 border rounded-lg bg-card">
                <p className="text-xs text-muted-foreground">평균 예측 수익률</p>
                <p
                  className={`text-2xl font-bold ${
                    stats.avgPredicted >= 0 ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {stats.avgPredicted >= 0 ? "+" : ""}
                  {stats.avgPredicted.toFixed(2)}%
                </p>
              </div>
              <div className="p-4 border rounded-lg bg-card">
                <p className="text-xs text-muted-foreground">평균 실제 수익률</p>
                <p
                  className={`text-2xl font-bold ${
                    stats.avgActual >= 0 ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {stats.avgActual >= 0 ? "+" : ""}
                  {stats.avgActual.toFixed(2)}%
                </p>
              </div>
              <div className="p-4 border rounded-lg bg-card">
                <p className="text-xs text-muted-foreground">평균 예측 오차</p>
                <p
                  className={`text-2xl font-bold ${
                    stats.avgError > 0 ? "text-blue-600" : "text-orange-600"
                  }`}
                >
                  {stats.avgError > 0 ? "+" : ""}
                  {stats.avgError.toFixed(2)}%p
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Filters and Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters - Left Sidebar */}
          <div className="lg:col-span-1">
            <IPOFilters companies={ipoData} onFilterChange={setFilters} />
          </div>

          {/* Charts - Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {/* Error Analysis Chart */}
            <ErrorAnalysisChart companies={filteredData} />

            {/* Quadrant Chart */}
            <QuadrantChart companies={filteredData} />

            {/* Accuracy Matrix */}
            <AccuracyMatrix companies={filteredData} />
          </div>
        </div>
      </div>
    </div>
  );
}
