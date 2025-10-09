import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { IPOCompany } from "@/types/ipo";
import { useState } from "react";

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

export interface FilterState {
  dateRange: {
    start: string;
    end: string;
  };
  industries: string[];
  sectors_38: string[];
  priceRange: {
    min: number;
    max: number;
  };
}

interface IPOFiltersProps {
  companies: IPOCompany[];
  onFilterChange: (filters: FilterState) => void;
}

export function IPOFilters({ companies, onFilterChange }: IPOFiltersProps) {
  // Extract unique values for filters
  const allIndustries = Array.from(new Set(companies.map(c => c.industry))).sort();
  const allSectors38 = Array.from(new Set(companies.map(c => c.sector_38).filter(s => s && s !== "N/A"))).sort();

  const allPrices = companies.map(c => c.ipo_price_confirmed);
  const minPrice = Math.min(...allPrices);
  const maxPrice = Math.max(...allPrices);

  const allDates = companies.map(c => c.listing_date);
  const minDate = allDates.sort()[0];
  const maxDate = allDates.sort()[allDates.length - 1];

  const [filters, setFilters] = useState<FilterState>({
    dateRange: {
      start: minDate,
      end: maxDate,
    },
    industries: [],
    sectors_38: [],
    priceRange: {
      min: minPrice,
      max: maxPrice,
    },
  });

  const [selectedIndustries, setSelectedIndustries] = useState<Set<string>>(new Set());
  const [selectedSectors38, setSelectedSectors38] = useState<Set<string>>(new Set());

  const handleIndustryToggle = (industry: string) => {
    const newSet = new Set(selectedIndustries);
    if (newSet.has(industry)) {
      newSet.delete(industry);
    } else {
      newSet.add(industry);
    }
    setSelectedIndustries(newSet);

    const newFilters = {
      ...filters,
      industries: Array.from(newSet),
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleSector38Toggle = (sector: string) => {
    const newSet = new Set(selectedSectors38);
    if (newSet.has(sector)) {
      newSet.delete(sector);
    } else {
      newSet.add(sector);
    }
    setSelectedSectors38(newSet);

    const newFilters = {
      ...filters,
      sectors_38: Array.from(newSet),
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleDateChange = (type: 'start' | 'end', value: string) => {
    const newFilters = {
      ...filters,
      dateRange: {
        ...filters.dateRange,
        [type]: value,
      },
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handlePriceChange = (type: 'min' | 'max', value: string) => {
    const numValue = parseInt(value) || 0;
    const newFilters = {
      ...filters,
      priceRange: {
        ...filters.priceRange,
        [type]: numValue,
      },
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleReset = () => {
    const defaultFilters: FilterState = {
      dateRange: {
        start: minDate,
        end: maxDate,
      },
      industries: [],
      sectors_38: [],
      priceRange: {
        min: minPrice,
        max: maxPrice,
      },
    };
    setFilters(defaultFilters);
    setSelectedIndustries(new Set());
    setSelectedSectors38(new Set());
    onFilterChange(defaultFilters);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>필터</CardTitle>
        <CardDescription>IPO 기업을 필터링하세요</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Date Range */}
        <div className="space-y-2">
          <Label>상장일 범위</Label>
          <div className="space-y-3">
            <div>
              <Label className="text-xs text-muted-foreground">시작일</Label>
              <Input
                type="date"
                value={filters.dateRange.start}
                onChange={(e) => handleDateChange('start', e.target.value)}
                min={minDate}
                max={maxDate}
              />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">종료일</Label>
              <Input
                type="date"
                value={filters.dateRange.end}
                onChange={(e) => handleDateChange('end', e.target.value)}
                min={minDate}
                max={maxDate}
              />
            </div>
          </div>
        </div>

        {/* Industry Filter */}
        <div className="space-y-2">
          <Label>업종 (KOSDAQ)</Label>
          <div className="max-h-[200px] overflow-y-auto border rounded-md p-3 space-y-2">
            {allIndustries.map((industry) => (
              <div key={industry} className="flex items-center space-x-2">
                <Checkbox
                  id={`industry-${industry}`}
                  checked={selectedIndustries.has(industry)}
                  onCheckedChange={() => handleIndustryToggle(industry)}
                />
                <div
                  className="w-4 h-4 rounded flex-shrink-0"
                  style={{ backgroundColor: INDUSTRY_COLORS[industry] || "#8884d8" }}
                ></div>
                <label
                  htmlFor={`industry-${industry}`}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                >
                  {industry}
                </label>
              </div>
            ))}
          </div>
          {selectedIndustries.size > 0 && (
            <p className="text-xs text-muted-foreground">
              {selectedIndustries.size}개 선택됨
            </p>
          )}
        </div>

        {/* Sector 38 Filter */}
        <div className="space-y-2">
          <Label>업종 (38.co.kr)</Label>
          <div className="max-h-[200px] overflow-y-auto border rounded-md p-3 space-y-2">
            {allSectors38.map((sector) => (
              <div key={sector} className="flex items-center space-x-2">
                <Checkbox
                  id={`sector38-${sector}`}
                  checked={selectedSectors38.has(sector)}
                  onCheckedChange={() => handleSector38Toggle(sector)}
                />
                <label
                  htmlFor={`sector38-${sector}`}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                >
                  {sector}
                </label>
              </div>
            ))}
          </div>
          {selectedSectors38.size > 0 && (
            <p className="text-xs text-muted-foreground">
              {selectedSectors38.size}개 선택됨
            </p>
          )}
        </div>

        {/* Price Range */}
        <div className="space-y-2">
          <Label>공모가 범위 (원)</Label>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label className="text-xs text-muted-foreground">최소</Label>
              <Input
                type="number"
                value={filters.priceRange.min}
                onChange={(e) => handlePriceChange('min', e.target.value)}
                min={minPrice}
                max={maxPrice}
                step={1000}
              />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">최대</Label>
              <Input
                type="number"
                value={filters.priceRange.max}
                onChange={(e) => handlePriceChange('max', e.target.value)}
                min={minPrice}
                max={maxPrice}
                step={1000}
              />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            ₩{filters.priceRange.min.toLocaleString()} ~ ₩{filters.priceRange.max.toLocaleString()}
          </p>
        </div>

        {/* Reset Button */}
        <Button variant="outline" onClick={handleReset} className="w-full">
          필터 초기화
        </Button>
      </CardContent>
    </Card>
  );
}
