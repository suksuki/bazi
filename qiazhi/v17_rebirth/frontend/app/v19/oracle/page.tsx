import type { Metadata } from "next";
import { OraclePrototype } from "@/components/v19/OraclePrototype";

export const metadata: Metadata = {
  title: "V19 Oracle Prototype",
  description: "Static V19 structured reasoning UI prototype.",
};

export default function V19OraclePrototypePage() {
  return <OraclePrototype />;
}

