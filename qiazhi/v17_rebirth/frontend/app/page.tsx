import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export default async function HomePage() {
  const cookieStore = await cookies();
  const hasSession = Boolean(cookieStore.get("v17_session")?.value);
  redirect(hasSession ? "/v17/oracle" : "/login");
}
