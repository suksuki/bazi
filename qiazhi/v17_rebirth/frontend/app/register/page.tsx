import { V17_AuthScreen } from "@/components/V17_AuthScreen";

type RegisterPageProps = {
  searchParams?: Promise<{ next?: string }>;
};

export default async function RegisterPage({ searchParams }: RegisterPageProps) {
  const params = searchParams ? await searchParams : undefined;
  return <V17_AuthScreen mode="register" nextPath={params?.next} />;
}
