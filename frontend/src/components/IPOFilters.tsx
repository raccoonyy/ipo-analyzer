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
  sectors: string[];
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
  const allSectors = Array.from(new Set(companies.map(c => c.sector_grouped).filter(s => s && s !== "N/A"))).sort();

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
    sectors: [],
    priceRange: {
      min: minPrice,
      max: maxPrice,
    },
  });

  const [selectedSectors, setSelectedSectors] = useState<Set<string>>(new Set());

  const handleSectorToggle = (sector: string) => {
    const newSet = new Set(selectedSectors);
    if (newSet.has(sector)) {
      newSet.delete(sector);
    } else {
      newSet.add(sector);
    }
    setSelectedSectors(newSet);

    const newFilters = {
      ...filters,
      sectors: Array.from(newSet),
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
      sectors: [],
      priceRange: {
        min: minPrice,
        max: maxPrice,
      },
    };
    setFilters(defaultFilters);
    setSelectedSectors(new Set());
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

        {/* Sector Filter */}
        <div className="space-y-2">
          <Label>업종</Label>
          <div className="max-h-[200px] overflow-y-auto border rounded-md p-3 space-y-2">
            {allSectors.map((sector) => (
              <div key={sector} className="flex items-center space-x-2">
                <Checkbox
                  id={`sector-${sector}`}
                  checked={selectedSectors.has(sector)}
                  onCheckedChange={() => handleSectorToggle(sector)}
                />
                <label
                  htmlFor={`sector-${sector}`}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                >
                  {sector}
                </label>
              </div>
            ))}
          </div>
          {selectedSectors.size > 0 && (
            <p className="text-xs text-muted-foreground">
              {selectedSectors.size}개 선택됨
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
