import { V17_AuthScreen } from "@/components/V17_AuthScreen";

type LoginPageProps = {
  searchParams?: Promise<{ next?: string }>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const params = searchParams ? await searchParams : undefined;
  return <V17_AuthScreen mode="login" nextPath={params?.next} />;
}
