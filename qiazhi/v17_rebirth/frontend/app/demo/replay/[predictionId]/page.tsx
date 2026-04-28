import { V18_ReplayShareViewer } from "@/components/V18_ReplayShareViewer";

type ReplayPageProps = {
  params: Promise<{ predictionId: string }>;
};

export default async function ReplayPage({ params }: ReplayPageProps) {
  const { predictionId } = await params;
  return <V18_ReplayShareViewer predictionId={predictionId} />;
}
