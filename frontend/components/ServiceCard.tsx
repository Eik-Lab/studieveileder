import Link from "next/link";
import { LucideIcon } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface ServiceCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  link: string;
  buttonText: string;
  iconColor: string;
  badge?: string;
}

export default function ServiceCard({
  icon: Icon,
  title,
  description,
  link,
  buttonText,
  iconColor,
  badge,
}: ServiceCardProps) {
  return (
    <Card className="flex flex-col h-full hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between mb-3">
          <div className={`p-3 rounded-lg bg-gray-100 ${iconColor}`}>
            <Icon size={28} />
          </div>
          {badge && (
            <Badge variant="secondary" className="text-xs">
              {badge}
            </Badge>
          )}
        </div>
        <CardTitle className="text-xl">{title}</CardTitle>
        <CardDescription className="text-base">{description}</CardDescription>
      </CardHeader>
      <CardContent className="mt-auto">
        <Button asChild className="w-full bg-[#006633] hover:bg-[#004d26]">
          <Link href={link}>{buttonText}</Link>
        </Button>
      </CardContent>
    </Card>
  );
}
