import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { IPOInputForm } from "@/components/IPOInputForm";
import { PredictionResult } from "@/components/PredictionResult";
import { IPOData, IPOCompany, IPODataResponse } from "@/types/ipo";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { BarChart3 } from "lucide-react";

const Index = () => {
  const [selectedCompany, setSelectedCompany] = useState<IPOCompany | null>(null);
  const [ipoData, setIpoData] = useState<IPOData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    // Load precomputed data from backend
    fetch(`${import.meta.env.BASE_URL}ipo_precomputed.json`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((response: IPODataResponse) => {
        if (!response.ipos || !Array.isArray(response.ipos)) {
          throw new Error('Invalid data format: expected ipos array');
        }
        // Filter out SPAC companies
        const filteredIpos = response.ipos.filter(
          (ipo) =>
            !ipo.company_name.includes('기업인수목적') &&
            !(ipo.industry && ipo.industry.includes('SPAC'))
        );
        setIpoData(filteredIpos);
        setIsLoading(false);
        if (filteredIpos && filteredIpos.length > 0) {
          setSelectedCompany(filteredIpos[0]);
        }
      })
      .catch(err => {
        console.error('Failed to load IPO data:', err);
        setIsLoading(false);
        setIpoData([]);
        toast({
          title: "오류",
          description: "IPO 데이터를 불러올 수 없습니다. 백엔드에서 데이터가 생성되었는지 확인하세요.",
          variant: "destructive",
        });
      });
  }, [toast]);

  const handleCompanySelect = (companyCode: string) => {
    if (!ipoData) return;

    const company = ipoData.find(c => c.code === companyCode);
    if (company) {
      setSelectedCompany(company);
      toast({
        title: "기업 선택됨",
        description: `${company.company_name}의 예측 결과를 표시합니다`,
      });
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">IPO 가격 예측</h1>
              <p className="text-muted-foreground mt-2">
                시장 데이터 기반 IPO 단기 가격 예측 (2022-2025)
              </p>
            </div>
            <Link to="/analysis">
              <Button variant="outline" className="gap-2">
                <BarChart3 className="h-4 w-4" />
                IPO 분석
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8 max-w-7xl mx-auto">
          <IPOInputForm
            companies={ipoData || []}
            selectedCompany={selectedCompany}
            onCompanySelect={handleCompanySelect}
            isLoading={isLoading}
          />
          <PredictionResult company={selectedCompany} />
        </div>
      </main>
    </div>
  );
};

export default Index;
