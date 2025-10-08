import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { IPOData, IPOCompany } from "@/types/ipo";
import { Loader2 } from "lucide-react";

interface IPOInputFormProps {
  companies: IPOData;
  selectedCompany: IPOCompany | null;
  onCompanySelect: (companyCode: string) => void;
  isLoading: boolean;
}

export function IPOInputForm({
  companies,
  selectedCompany,
  onCompanySelect,
  isLoading,
}: IPOInputFormProps) {
  if (isLoading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>IPO 기업 선택</CardTitle>
          <CardDescription>IPO 데이터 로딩 중...</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center min-h-[200px]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }

  if (!companies || !Array.isArray(companies) || companies.length === 0) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>IPO 기업 선택</CardTitle>
          <CardDescription>IPO 데이터 없음</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center min-h-[200px] text-muted-foreground">
          기업을 찾을 수 없습니다. 백엔드에서 예측 데이터가 생성되었는지 확인하세요.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>IPO 기업 선택</CardTitle>
        <CardDescription>
          IPO 가격 예측을 보려면 기업을 선택하세요
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-medium">기업</label>
          <Select
            value={selectedCompany?.code || ""}
            onValueChange={onCompanySelect}
          >
            <SelectTrigger>
              <SelectValue placeholder="기업을 선택하세요" />
            </SelectTrigger>
            <SelectContent>
              {companies.map((company) => (
                <SelectItem key={`${company.id}-${company.code}`} value={company.code}>
                  {company.company_name} ({company.code}) - {company.listing_date}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {selectedCompany && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 border rounded-lg bg-muted/50">
            <div>
              <p className="text-sm text-muted-foreground">기업명</p>
              <p className="font-medium">{selectedCompany.company_name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">종목코드</p>
              <p className="font-medium">{selectedCompany.code}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">상장일</p>
              <p className="font-medium">{selectedCompany.listing_date}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">공모가</p>
              <p className="font-medium">
                ₩{selectedCompany.ipo_price_confirmed.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">희망공모가액</p>
              <p className="font-medium">
                ₩{selectedCompany.ipo_price_lower.toLocaleString()} - ₩
                {selectedCompany.ipo_price_upper.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">업종</p>
              <p className="font-medium">{selectedCompany.industry}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">테마</p>
              <p className="font-medium">{selectedCompany.theme}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">공모주식수</p>
              <p className="font-medium">
                {selectedCompany.shares_offered.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">기관경쟁률</p>
              <p className="font-medium">
                {selectedCompany.institutional_demand_rate.toFixed(2)}:1
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">청약경쟁률</p>
              <p className="font-medium">
                {selectedCompany.subscription_competition_rate.toFixed(2)}:1
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">의무보유비율</p>
              <p className="font-medium">
                {selectedCompany.lockup_ratio.toFixed(2)}%
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
