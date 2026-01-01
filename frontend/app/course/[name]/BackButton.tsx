"use client";

import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function BackButton() {
  const router = useRouter();

  return (
    <Button
      variant="ghost"
      onClick={() => router.back()}
      className="mb-6 pl-0 text-muted-foreground hover:text-foreground"
    >
      <ChevronLeft className="mr-2 h-4 w-4" />
      Tilbake
    </Button>
  );
}
